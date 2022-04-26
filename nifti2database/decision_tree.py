# standard modules

# dependency modules
import pandas   # for DataFrame
import nibabel  # to load nifti header

# local modules
import niix2bids
from niix2bids.classes import Volume
from niix2bids.utils import get_logger


########################################################################################################################
def prog_mprage(seqinfo: pandas.DataFrame) -> None:
    pass


########################################################################################################################
def prog_tse_vfl(seqinfo: pandas.DataFrame) -> None:
    pass


########################################################################################################################
def prog_diff(seqinfo: pandas.DataFrame) -> None:
    pass


########################################################################################################################
def prog_bold(seqinfo: pandas.DataFrame) -> None:
    pass


########################################################################################################################
def prog_fmap(seqinfo: pandas.DataFrame) -> None:
    pass


########################################################################################################################
def prog_gre(seqinfo: pandas.DataFrame) -> None:
    pass


########################################################################################################################
def prog_tse(seqinfo: pandas.DataFrame) -> None:
    pass


########################################################################################################################
def prog_ep2d_se(seqinfo: pandas.DataFrame) -> None:
    pass


########################################################################################################################
def prog_DISCARD(seqinfo: pandas.DataFrame) -> None:
    pass


########################################################################################################################
def prog_UNKNOWN(df: pandas.DataFrame) -> None:
    pass


########################################################################################################################
def run(volume_list: list[Volume], config: list) -> None:

    log = get_logger()
    log.info(f'starting decision tree...')

    # extract volume_list.seqparam into a DataFrame, for easy grouping
    list_seqparam = [vol.seqparam for vol in volume_list]
    df = pandas.DataFrame(list_seqparam)

    # call each routine depending on the sequence name
    for seq_regex, fcn_name in config:      # loop over sequence decision tree

        # get list of corresponding sequence
        seqinfo = niix2bids.decision_tree.utils.slice_with_genericfield(df, 'PulseSequenceDetails', seq_regex)
        if seqinfo.empty: continue          # just to run the code faster

        columns = ['PatientName', 'ProtocolName', 'run']
        groups = df.groupby(columns)
    
        for scan, serie in groups:
            func = eval(fcn_name)               # fetch the name of the prog_ to call dynamically
            func(seqinfo)       # execute the prog_

    log.info(f'...decision tree done')