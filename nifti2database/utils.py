# standard modules
import logging
import warnings
import os
import json

# dependency modules
import niix2bids
from niix2bids.classes import Volume
from niix2bids.utils import logit
import nibabel
import numpy as np
import pandas
import psycopg2

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
def read_all_nifti_header(df: pandas.DataFrame) -> pandas.DataFrame:

    Matrix     = []
    Resolution = []
    FoV        = []

    for row in df.index:

        # shortcut
        vol = df.loc[row,'Volume']

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

        # # this is nuts : i cannot assign a 'list' to a specific row & column
        # df.loc[row,'Matrix'     ] = matrix
        # df.loc[row,'Resolution' ] = resolution
        # df.loc[row,'FoV'        ] = fov

        df.loc[row,'Mx'] = matrix[0]
        df.loc[row,'My'] = matrix[1]
        df.loc[row,'Mz'] = matrix[2]
        if len(matrix) == 4:
            df.loc[row,'Mt'] = matrix[3]
        df.loc[row,'Rx'] = resolution[0]
        df.loc[row,'Ry'] = resolution[1]
        df.loc[row,'Rz'] = resolution[2]
        if len(resolution) == 4:
            df.loc[row,'Rt'] = resolution[3]
        df.loc[row,'Fx'] = fov[0]
        df.loc[row,'Fy'] = fov[1]
        df.loc[row,'Fz'] = fov[2]
        if len(fov) == 4:
            df.loc[row,'Ft'] = fov[3]

        Matrix.append(matrix)
        Resolution.append(resolution)
        FoV.append(fov)

    df['Matrix'    ] = Matrix
    df['Resolution'] = Resolution
    df['FoV'       ] = FoV

    return df


########################################################################################################################
def concat_bidsfields_to_seqparam(df: pandas.DataFrame) -> pandas.DataFrame:
    
    for row in df.index:

        # shortcut
        vol = df.loc[row,'Volume']

        for key in vol.bidsfields:
            df.loc[row,key] = vol.bidsfields[key]
        df.loc[row,'tag'   ] = vol.tag
        df.loc[row,'suffix'] = vol.suffix
        df.loc[row,'sub'   ] = vol.sub
        
    return df


########################################################################################################################
def build_scan_from_series(df: pandas.DataFrame, config: list) -> list[dict]:

    log = niix2bids.utils.get_logger()
    log.info(f'starting decision tree...')

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

            to_delete = []

            for key in scan.keys():

                try:
                    unique_stuff = series[key].unique()
                    if len(unique_stuff) == 1:
                        scan[key] = unique_stuff[0]

                except TypeError:  # unique() on 'list' is not possible, but it is on 'tuple'
                    unique_stuff = series[key].transform(tuple).unique()
                    if len(unique_stuff) == 1:
                        scan[key] = unique_stuff[0]

                # remove nan
                if (type(scan[key]) is np.float64 or type(scan[key]) is float) and np.isnan(scan[key]):
                    to_delete.append(key)

                # convert some fields into regular builtin objects
                if type(scan[key]) is np.int64:
                    scan[key] = int(scan[key])

            for key in to_delete:  # remove keys with juste a s 1x1 nan
                del scan[key]
    
            scans.append(scan)

    return scans

    log.info(f'...decision tree done')


########################################################################################################################
def remove_duplicate(scans: list[dict]) -> list[dict]:

    scan_id = [ scan['SeriesInstanceUID'] if type(scan['SeriesInstanceUID']) is str else scan['SeriesInstanceUID'][0]
                for scan in scans ]

    scan_id = np.array(scan_id)
    uniques, uniq_idx = np.unique(scan_id,return_index=True)

    scans_unique = []
    for idx in uniq_idx:  # sort in descending order
        scans_unique.append(scans[idx])

    return scans_unique

########################################################################################################################
def connect_to_datase() -> psycopg2.extensions.connection:

    log = niix2bids.utils.get_logger()

    # fetch crendtial in home directory
    cred_path = os.path.join(os.path.expanduser("~"),"credentials_nifti2database")
    log.info(f"Loading credentials : {cred_path}")
    with open(cred_path,'r') as fid:
        cred_dic = json.load(fid)

    # connect to DB
    log.info(f"Connecting to database...")
    con = psycopg2.connect(
        database=cred_dic['database'],
        user    =cred_dic['user'    ],
        password=cred_dic['password'],
        host    =cred_dic['host'    ],
        port    =cred_dic['port'    ]
    )
    log.info(f"... done")

    return con


########################################################################################################################
def insert_scan_to_database(con: psycopg2.extensions.connection, scans: list[dict]) -> None:

    # open "cursor" to prepare SQL request
    cur = con.cursor()

    # first, we check if the scan already exist

    # get list of scans in the db
    cur.execute(f"SELECT seriesinstanceuid FROM nifti2database_schema.nifti_json;")
    db_id = cur.fetchall()
    db_id = frozenset([id[0] for id in db_id])  # fronzenset is supposed to be fast for

    if len(db_id)>0:  # just to check if the db is empty or not

        # establish scan_id
        scan_id = [ scan['SeriesInstanceUID'] if type(scan['SeriesInstanceUID']) is str else scan['SeriesInstanceUID'][0]
                    for scan in scans ]

        # remove if already exist
        to_remove = [ sid in db_id for sid in scan_id ]  # list[bool]
        scan_new = []
        for idx, status in enumerate(to_remove):
            if status is False:
                scan_new.append(scans[idx])

    else:
        scan_new = scans

    # insert scans
    for scan in scan_new:

        # change some variables type so they can fit in the SQL request ================================================
        scan_clean = scan.copy()

        # change Volume objects to a standard path str
        if type(scan['Volume']) is niix2bids.classes.Volume:
            scan_clean['Volume'] = scan['Volume'].nii.path
        else: # its a list[Volume]
            path_list = []
            for vol in scan['Volume']:
                path_list.append(vol.nii.path)
            scan_clean['Volume'] = path_list

        dict_str = json.dumps(scan_clean)

        # change NaN to 'NaN'
        dict_str = dict_str.replace('NaN', '"NaN"')

        first_SeriesInstanceUID = scan_clean['SeriesInstanceUID'] if type(scan_clean['SeriesInstanceUID']) is str else scan_clean['SeriesInstanceUID'][0]

        # insert request
        cur.execute(f"INSERT INTO nifti2database_schema.nifti_json (dict, seriesinstanceuid, insertion_time) VALUES('{dict_str}', '{first_SeriesInstanceUID}', now());")
        con.commit()

    cur.close()
    con.close()
