# standard modules
import logging
import warnings
import os
import json
import random
import string

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
@logit("Reading all nifti headers to extract info absent from the JSON. This may take a while... ", level=logging.INFO)
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
        fov = tuple([ mx*res for mx,res in zip(matrix, resolution)])

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
@logit("Concatenante BIDSfields from niix2bids to the json dict", level=logging.INFO)
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
@logit("Regroup each nifti into a group of 'scan'. 1 'scan'= 1 MRI sequence", level=logging.INFO)
def build_scan_from_series(df: pandas.DataFrame, config: list) -> list[dict]:

    scans = []  # list[dict]

    # call each routine depending on the sequence name
    for seq_regex, fcn_name in config:  # loop over sequence decision tree

        # get list of corresponding sequence
        seqinfo = niix2bids.decision_tree.utils.slice_with_genericfield(df, 'PulseSequenceName', seq_regex)
        if seqinfo.empty: continue  # just to run the code faster

        # we group using raw json info and the "run" number from the bids decision tree in niix2bids
        columns = ['PatientName', 'ProtocolName', 'run', 'MRAcquisitionType', 'StudyInstanceUID']
        # 'MRAcquisitionType' is can help sometimes for grouping

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

            for key in to_delete:  # remove keys with just a 1x1 nan
                del scan[key]
    
            scans.append(scan)

    return scans


########################################################################################################################
@logit("Regroup each nifti into a group of 'scan'. 1 'scan'= 1 MRI sequence", level=logging.INFO)
def remove_duplicate(scans: list[dict]) -> list[dict]:

    log = niix2bids.utils.get_logger()

    scan_id = [ scan['SeriesInstanceUID'] if type(scan['SeriesInstanceUID']) is str else scan['SeriesInstanceUID'][0]
                for scan in scans ]

    scan_id = np.array(scan_id)
    uniques, uniq_idx = np.unique(scan_id,return_index=True)

    scans_unique = []
    for idx in uniq_idx:  # sort in descending order
        scans_unique.append(scans[idx])

    log.info(f"nScan={len(scans):,} // nUnique={len(scans_unique):,} // nDuplicate={len(scans)- len(scans_unique):,}")

    return scans_unique

########################################################################################################################
@logit("Connection to database using psycopg2.connect()", level=logging.INFO)
def connect_to_datase(connect_or_prepare: str, credentials:  str) -> psycopg2.extensions.connection:

    log = niix2bids.utils.get_logger()

    if connect_or_prepare == "connect":

        # fetch crendtial in home directory
        log.info(f"Loading credentials : {credentials}")
        with open(credentials,'r') as fid:
            cred_dic = json.load(fid)

        # connect to DB
        log.info(f"Connecting to database...")
        con = psycopg2.connect(
            database   = cred_dic['database'],
            user       = cred_dic['user'    ],
            password   = cred_dic['password'],
            host       = cred_dic['host'    ],
            port       = cred_dic['port'    ],
            sslmode    = 'disable',
            # gssencmode = 'disable',
        )
        log.info(f"... done")

        return con, cred_dic['schema'], cred_dic['table']

    else:

        return None


########################################################################################################################
@logit("Get list of scans in database, and add the 'new' ones", level=logging.INFO)
def insert_scan_to_database(con: psycopg2.extensions.connection, schema: str, talble: str, scans: list[dict]) -> list[str]:

    log = niix2bids.utils.get_logger()

    if con is not None:

        # open "cursor" to prepare SQL request
        cur = con.cursor()

        # first, we check if the scan already exist ------------------------------------------------------------------------

        log.info("Fetching existing scans in database")

        # get list of scans in the db
        cur.execute(f"SELECT suid FROM {schema}.{talble};")
        db_id = cur.fetchall()
        db_id = frozenset([id[0] for id in db_id])  # fronzenset is supposed to be faster for comparaison operations

        log.info(f"Found {len(db_id):,} scans in database")

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

    else:
        scan_new = scans

    log.info(f"nScanDB={len(scans):,} // nScanToAdd={len(scans):,} // nScanNew={len(scan_new):,}")

    # insert new scans -------------------------------------------------------------------------------------------------
    insert_list = []
    for scan in scan_new:

        # change some variables type so they can fit in the SQL request
        scan_clean = scan.copy()

        # change Volume objects to a standard path str
        if type(scan['Volume']) is niix2bids.classes.Volume:
            scan_clean['Volume'] = scan['Volume'].nii.path
        else: # its a list[Volume]
            path_list = []
            for vol in scan['Volume']:
                path_list.append(vol.nii.path)
            scan_clean['Volume'] = path_list

        # clean values =================================================================================================
        # this step looks overkill, but the simplification makes the jsonb (in the database) much cleaner
        # => request in the database will be simplified, since the rounding will be done

        # this function will convert scalar
        def int_or_round3__scalar(scalar):
            if (type(scalar) is np.float64 or type(scalar) is float) and np.isnan(scalar):
                return scalar
            scalar = float(scalar)  # conversion to the builtin float to avoid numpy.float64
            scalar = round(scalar) if round(scalar) == round(scalar,3) else round(scalar,3)
            return scalar

        # this function will 'apply int_or_round3__scalar' on each element or sub-element
        def int_or_round3(input):
            if type(input) == np.float64:  # this is a scalar
                return int_or_round3__scalar(input)
            else: # tuple ? list[typle] ?
                output_list = []
                for elem in input:
                    if type(elem) is tuple: # tuple
                        output_list.append( tuple(map(int_or_round3__scalar,elem)) )
                    else:
                        output_list.append( int_or_round3__scalar(elem) )
                return output_list

        scan_clean['Mx'] = int_or_round3(scan_clean['Mx'])
        scan_clean['My'] = int_or_round3(scan_clean['My'])
        scan_clean['Mz'] = int_or_round3(scan_clean['Mz'])
        if 'Mt' in scan_clean.keys():
            scan_clean['Mt'] = int_or_round3(scan_clean['Mt'])

        scan_clean['Rx'] = int_or_round3(scan_clean['Rx'])
        scan_clean['Ry'] = int_or_round3(scan_clean['Ry'])
        scan_clean['Rz'] = int_or_round3(scan_clean['Rz'])
        if 'Rt' in scan_clean.keys():
            scan_clean['Rt'] = int_or_round3(scan_clean['Rt'])

        scan_clean['Fx'] = int_or_round3(scan_clean['Fx'])
        scan_clean['Fy'] = int_or_round3(scan_clean['Fy'])
        scan_clean['Fz'] = int_or_round3(scan_clean['Fz'])
        if 'Ft' in scan_clean.keys():
            scan_clean['Ft'] = int_or_round3(scan_clean['Ft'])

        scan_clean['Matrix'    ] = int_or_round3(scan_clean['Matrix'    ])
        scan_clean['Resolution'] = int_or_round3(scan_clean['Resolution'])
        scan_clean['FoV'       ] = int_or_round3(scan_clean['FoV'       ])

        scan_clean['run'] = int(scan_clean['run'])

        # ==========================================================================================================

        dict_str = json.dumps(scan_clean)

        # change NaN to 'NaN'
        dict_str = dict_str.replace('NaN', '"NaN"')

        first_SeriesInstanceUID = scan_clean['SeriesInstanceUID'] if type(scan_clean['SeriesInstanceUID']) is str else scan_clean['SeriesInstanceUID'][0]

        # 'AcquisitionDateTime': '2021-10-25T09:36:22.535000' => split with the T, replace - by _
        if type(scan_clean['AcquisitionDateTime']) is str:
            patient_id = scan_clean['AcquisitionDateTime']   .split('T')[0].replace('-','_') + "_" + scan_clean['PatientName']
        elif type(scan_clean['AcquisitionDateTime']) is list:
            patient_id = scan_clean['AcquisitionDateTime'][0].split('T')[0].replace('-','_') + "_" + scan_clean['PatientName']

        log.info(f"Adding scan to database : { scan_clean['Volume'] } ")

        insert_line = f"INSERT INTO {schema}.{talble} (dict, suid, patient_id, insertion_time) VALUES('{dict_str}', '{first_SeriesInstanceUID}', '{patient_id}', now());"
        insert_list.append(insert_line)

        if con is not None:

            # insert request
            cur.execute(insert_line)
            con.commit()

    if con is not None:
        cur.close()
        con.close()

    log.info("Connection to dabase closed")

    return insert_list


########################################################################################################################
@logit(f"Writing INSERT lines to file",level=logging.INFO)
def write_insert_list(logfile: str, insert_list: list[str]) -> None:

    log = niix2bids.utils.get_logger()

    # generate random id
    id = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(8))

    # add id as suffix to logfile
    name, ext = os.path.splitext(logfile)
    insert_file = f"{name}_{id}{ext}"
    insert_fullpath = os.path.join(os.path.dirname(logfile), insert_file)

    log.info(f"writing INSERT lines in : {insert_fullpath}")

    # write
    with open(insert_fullpath , mode='wt', encoding='utf-8' ) as fp:
        fp.write('\n'.join(insert_list))
