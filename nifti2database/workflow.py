# standard modules
import argparse  # just for function signature
import os        # for path management
import sys       # to stop script execution on case of error
import time      # to time execution of code
import logging   # to access the log report

# dependency modules
import niix2bids.utils

# local modules
import nifti2database


########################################################################################################################
def run(args: argparse.Namespace, sysexit: bool = True) -> str:

    # ------------------------------------------------------------------------------------------------------------------
    # from here, this a basically a copy-paste of niix2bids.workflow.run()

    star_time = time.time()

    # create output dir id needed
    if args.out_dir and not os.path.exists(args.out_dir):
        os.mkdir(args.out_dir)

    log = niix2bids.utils.get_logger()
    log.info(f"nifti2database=={nifti2database.metadata.get_nifti2database_version()}")

    # logs
    log.info(f"in_dir  : {args.in_dir}")
    log.info(f"out_dir : {args.out_dir}")
    if args.out_dir:
        logfile = log.__class__.root.handlers[1].baseFilename
        log.info(f"logfile : {logfile}")
    log.info(f"connect_or_prepare : {args.connect_or_prepare}")

    if args.connect_or_prepare == 'prepare' and args.out_dir is None:
        log.error(f"if '--prepare' is used , '--out_dir' has to be defined too")
        if sysexit:
            sys.exit(1)
        else:
            return nifti2database.utils.get_report()

    # check for credentials file
    if args.connect_or_prepare == "connect":
        if not os.path.exists(args.credentials):
            log.error(f"credentials file does not exist : {args.credentials}")
            if sysexit:
                sys.exit(1)
            else:
                return nifti2database.utils.get_report()
        else:
            log.info(f"credentials : {args.credentials}")

    # check if input dir exists
    for one_dir in args.in_dir:
        if not os.path.exists(one_dir):
            log.error(f"in_dir does not exist : {one_dir}")
            if sysexit:
                sys.exit(1)
            else:
                return nifti2database.utils.get_report()

    # load config file
    config = niix2bids.utils.load_config_file(args.config_file)

    # read all dirs and establish file list
    file_list = niix2bids.utils.fetch_all_files(args.in_dir)

    # isolate .nii files
    file_list_nii = niix2bids.utils.isolate_nii_files(file_list)

    # check if all .nii files have their own .json
    file_list_nii, file_list_json = niix2bids.utils.check_if_json_exists(file_list_nii)

    # create Volume objects
    volume_list = niix2bids.utils.create_volume_list(file_list_nii)

    # read all json files
    niix2bids.utils.read_all_json(volume_list)

    # apply decision tree
    # !! here, only Siemens is implemented !!
    df = niix2bids.decision_tree.siemens.run(volume_list, config)

    # to here
    # ------------------------------------------------------------------------------------------------------------------

    # logs from niix2bids.utils.apply_bids_architecture
    nifti2database.utils.display_logs_from_decision_tree(volume_list)
    
    # read all nifti headers
    df = nifti2database.utils.read_all_nifti_header(df)

    # concatenate the bidsfields with the jsondict (seqparam)
    df = nifti2database.utils.concat_bidsfields_to_seqparam(df)

    # ok here is the most important part : regroup volumes by scan
    scans = nifti2database.utils.build_scan_from_series(df, config)

    # duplicate happen during dev, but should not happen for production
    # anyway, check it and log it
    scans = nifti2database.utils.remove_duplicate(scans)

    # connect to database
    con, schema, table = nifti2database.utils.connect_to_datase(args.connect_or_prepare, args.credentials)

    # insert scans to database
    insert_list = nifti2database.utils.insert_scan_to_database(con, schema, table, scans)

    if args.connect_or_prepare == "prepare":
        nifti2database.utils.write_insert_list(logfile, insert_list)

    stop_time = time.time()

    log.info(f'Total execution time is : {stop_time-star_time:.3f}s')

    # THE END
    if sysexit:
        sys.exit(0)
    else:
        return nifti2database.utils.get_report()
