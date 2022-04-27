# standard modules
import warnings

# dependency modules
import niix2bids
from niix2bids.classes import Volume
import nibabel
import numpy as np
import pandas

# local modules


########################################################################################################################
def read_all_nifti_header(volume_list: list[Volume]) -> None:
    for vol in volume_list:
        
        # load header
        nii = nibabel.load(vol.nii.path)

        # fetch raw parmeters
        matrix = nii.header.get_data_shape()
        resolution = nii.header.get_zooms()
        fov = [ mx*res for mx,res in zip(matrix, resolution)]

        # format parameters
        matrix = list(matrix)
        resolution = np.round(resolution, 3).astype(float).tolist()
        fov = [int(x) for x in fov]

        # save parameters
        vol.seqparam['Matrix'    ] = matrix
        vol.seqparam['Resolution'] = resolution
        vol.seqparam['FoV'       ] = fov


########################################################################################################################
def concat_bidsfields_to_seqparam(volume_list: list[Volume]) -> None:
    for vol in volume_list:
        vol.seqparam.update( vol.bidsfields )
        vol.seqparam['tag'   ] = vol.tag
        vol.seqparam['suffix'] = vol.suffix
        vol.seqparam['sub'   ] = vol.sub


########################################################################################################################
def build_scan_from_series(volume_list: list[Volume], config: list) -> list[dict]:

    log = niix2bids.utils.get_logger()
    log.info(f'starting decision tree...')

    # extract volume_list.seqparam into a DataFrame, for easy grouping
    list_seqparam = [vol.seqparam for vol in volume_list]
    df = pandas.DataFrame(list_seqparam)

    # %CustomerSeq%_cmrr_mbep2d_bold -> cmrr_mbep2d_bold
    df['PulseSequenceName'] = df['PulseSequenceDetails'].apply(lambda s: s.rsplit("%_")[1])

    scans = []

    # call each routine depending on the sequence name
    for seq_regex, fcn_name in config:  # loop over sequence decision tree

        # get list of corresponding sequence
        seqinfo = niix2bids.decision_tree.utils.slice_with_genericfield(df, 'PulseSequenceName', seq_regex)
        if seqinfo.empty: continue  # just to run the code faster

        # we group using raw json info and the "run" number from the bids decision tree in niix2bids
        columns = ['PatientName', 'ProtocolName', 'run']
        groups = seqinfo.groupby(columns)

        for _, series in groups:

            scan = series.to_dict('list') # convert the DataFrame to standard dict

            nRow = series.shape[0]
            to_delete = []

            for key in scan.keys():

                with warnings.catch_warnings():  # supress a warning, wich does not make sense to me...
                    warnings.filterwarnings('ignore',r"Creating an ndarray from ragged nested sequences")
                    unique_stuff = np.unique( scan[key] )

                if len(unique_stuff) == 1:  # if info is same acroos all nifti, keep it reduced, for readability
                    scan[key] = unique_stuff
                else:
                    pass # just keep everything

                # special case : if there is only a 'non', delete the key, since the information is not relevent
                if type(scan[key]) is np.ndarray and len(scan[key]) is 1:
                    scan[key] = scan[key][0]
                    if type(scan[key]) == np.float64 and np.isnan(scan[key]):
                        to_delete.append(key)

            for key in to_delete:
                del scan[key]
    
            scans.append(scan)

    return scans


    log.info(f'...decision tree done')
