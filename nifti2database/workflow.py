# standard modules
import argparse  # just for function signature
import os        # for path management
import sys       # to stop script execution on case of error
import time      # to time execution of code

# dependency modules
import niix2bids.utils

# local modules
import nifti2database


########################################################################################################################
def run(args: argparse.Namespace) -> None:

    #-------------------------------------------------------------------------------------------------------------------
    # from here, this a basicly a copy-paste of niix2bids.workflow.run()

    star_time = time.time()

    # initialize logger (console & file)
    niix2bids.utils.init_logger(args.out_dir, args.logfile)
    log = niix2bids.utils.get_logger()
    log.info(f"nifti2database=={nifti2database.metadata.get_nifti2database_version()}")

    # logs
    log.info(f"in_dir  : {args.in_dir}")
    log.info(f"out_dir : {args.out_dir}")
    if args.logfile:
        log.info(f"logfile : {log.__class__.root.handlers[1].baseFilename}")

    # check if input dir exists
    for one_dir in args.in_dir:
        if not os.path.exists(one_dir):
            log.error(f"in_dir does not exist : {one_dir}")
            sys.exit(1)

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
    niix2bids.decision_tree.siemens.run(volume_list, config)
    df = niix2bids.decision_tree.siemens.run(volume_list, config)

    # to here
    #-------------------------------------------------------------------------------------------------------------------

    # logs from niix2bids.utils.apply_bids_architecture
    nifti2database.utils.display_logs_from_decision_tree(volume_list)
    
    # read all nifti headers
    nifti2database.utils.read_all_nifti_header(volume_list)
    df = nifti2database.utils.read_all_nifti_header(df)

    # conctenate the bidsfields with the jsondict (seqparam)
    nifti2database.utils.concat_bidsfields_to_seqparam(volume_list)
    df = nifti2database.utils.concat_bidsfields_to_seqparam(df)

    # ok here is the most important part : regroup volumes by scan
    scans = nifti2database.utils.build_scan_from_series(volume_list, config)

    stop_time = time.time()

    log.info(f'Total execution time is : {stop_time-star_time:.3f}s')

    # THE END
    sys.exit(0)
