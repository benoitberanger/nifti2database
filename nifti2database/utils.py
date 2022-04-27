# standard modules
import logging
import warnings

# dependency modules
import niix2bids
from niix2bids.classes import Volume
from niix2bids.utils import logit
import nibabel
import numpy as np
import pandas

# local modules

########################################################################################################################
def display_logs_from_decision_tree(volume_list: list[Volume]) -> None:

    log                       = niix2bids.utils.get_logger()
    log_info                  = []
    log_info_discard          = []
    log_warning               = []
    log_warning_unknown       = []
    log_error_not_interpreted = []

    for vol in volume_list:

        if len(vol.tag) > 0:  # only process correctly parsed volumes

            if vol.tag == 'DISCARD':
                log_info_discard.append(f'{vol.reason_not_ready} : {vol.nii.path}')

            elif vol.tag == 'UNKNOWN':
                log_warning_unknown.append(f'{vol.reason_not_ready} : {vol.nii.path}')

        elif len(vol.reason_not_ready) > 0:
            log_warning.append(f'{vol.reason_not_ready} : {vol.nii.path}')

        else:
            log_error_not_interpreted.append(f'file not interpreted : {vol.nii.path}')

    # print them all, but in order
    for msg in log_error_not_interpreted:
        log.error(msg)
    for msg in log_warning_unknown:
        log.warning(msg)
    for msg in log_warning:
        log.warning(msg)
    # for msg in log_info_discard:
    #     log.info(msg)
    for msg in log_info:
        log.info(msg)


########################################################################################################################
@logit("Reading all nifti headers to extract info absent from the JSON. This may take a while... ",level=logging.INFO)
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

    scans = []  # list[dict]

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

                try:
                    unique_stuff = series[key].unique()
                    if len(unique_stuff) == 1:
                        scan[key] = unique_stuff[0]
                    else:
                        pass

                except TypeError:  # unique() on 'list' is not possible, but it is on 'tuple'
                    unique_stuff = series[key].transform(tuple).unique()
                    if len(unique_stuff) == 1:
                        scan[key] = unique_stuff[0]
                    else:
                        pass

                # remove nan
                if type(scan[key]) is np.float64 or type(scan[key]) is float and np.isnan(scan[key]):
                    to_delete.append(key)

            for key in to_delete:  # remove keys with juste a s 1x1 nan
                del scan[key]
    
            scans.append(scan)

    return scans

    log.info(f'...decision tree done')
