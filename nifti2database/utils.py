# standard modules
import logging                  # logging lib (terminal & file)
import os                       # for path management
import shutil                   # for copyfile
from datetime import datetime   # to get current time
import sys                      # to stop script execution on case of error
import re                       # regular expressions
import json                     # to write json files
import time                     # to time execution of code
from functools import wraps     # for decorator
import traceback                # to get the current function name
import inspect                  # to get the current module name
import runpy                    # to run config script

# dependency modules
import pandas

# local modules
from nifti2database.classes import Volume


########################################################################################################################
def init_logger(out_dir: str, write_file: bool) -> None:

    # create output dir id needed
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    # create logger
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # create console handler
    consoleHandler = logging.StreamHandler()  # create
    consoleHandler.setLevel(logging.DEBUG)    # and set level to debug
    consoleHandler.setFormatter(formatter)    # add formatter handlers
    log.addHandler(consoleHandler)            # add handlers to logger

    # same thing but for a file handler
    if write_file:
        logfile = os.path.join(out_dir, "log_" + datetime.now().strftime('%Y-%m-%d_%Hh%Sm%S') + ".txt")

        fileHandeler = logging.FileHandler(logfile)
        fileHandeler.setLevel(logging.DEBUG)
        fileHandeler.setFormatter(formatter)
        log.addHandler(fileHandeler)


########################################################################################################################
def get_logger() -> logging.Logger:

    fcn_name = traceback.extract_stack(None, 2)[0][2]  # get function name of the caller

    upperstack = inspect.stack()[1]
    mdl_name = inspect.getmodule(upperstack[0]).__name__  # get module name of the caller

    name = mdl_name + ':' + fcn_name  # ex : nifti2database.utils:apply_bids_architecture
    log = logging.getLogger(name)

    return log


########################################################################################################################
def logit(message, level=logging.INFO):

    def log_time(func):

        @wraps(func)  # to keep function info, such as __name__
        def wrapper(*args, **kwargs):
            log = logging.getLogger(__name__ + ':' + func.__name__)

            msg = message + ' # start...'
            log.log(level, msg)

            start_time = time.time()
            res = func(*args, **kwargs)
            stop_time = time.time()

            msg = message + f" # ...done in {stop_time-start_time:.3f}s"
            log.log(level, msg)

            return res

        return wrapper

    return log_time


########################################################################################################################
def load_config_file(config_file: str) -> list:
    log = get_logger()

    if os.path.exists(config_file):
        if os.path.isfile(config_file):
            script_content = runpy.run_path(config_file)
            if "config" in script_content:
                config = script_content['config']
                log.info(f"using config_file : {config_file}")
                return config
            else:
                log.critical(f"config_file incorrect (no 'config' variable inside) : {config_file}")
                sys.exit(1)
        else:
            log.critical(f"config_file is not a file : {config_file}")
            sys.exit(1)
    else:
        log.critical(f"config_file does not exist : {config_file}")
        sys.exit(1)


########################################################################################################################
@logit('Fetch all files recursively. This might take time, it involves exploring the whole disk tree.', logging.INFO)
def fetch_all_files(in_dir: str) -> list[str]:

    file_list = []
    for one_dir in in_dir:
        for root, dirs, files in os.walk(one_dir):
            for file in files:
                file_list.append(os.path.join(root, file))

    if len(file_list) == 0:
        log = get_logger()
        log.error(f"no file found in {in_dir}")
        sys.exit(1)

    file_list.sort()
    return file_list


########################################################################################################################
@logit('Keep only nifti files (.nii, .nii.gz).', logging.INFO)
def isolate_nii_files(in_list: list[str]) -> list[str]:
    log = get_logger()

    r = re.compile(r"(.*nii$)|(.*nii.gz$)$")
    file_list_nii = list(filter(r.match, in_list))

    log.info(f"found {len(file_list_nii)} nifti files")
    if len(file_list_nii) == 0:
        log.error(f"no .nii file found in {in_list}")
        sys.exit(1)

    return file_list_nii


########################################################################################################################
@logit('Check if .json exist for each nifti file.', logging.INFO)
def check_if_json_exists(file_list_nii: list[str]) -> tuple[list[str], list[str]]:
    log = get_logger()

    file_list_json = []
    for file in file_list_nii:
        root, ext = os.path.splitext(file)
        if ext == ".gz":
            jsonfile = os.path.splitext(root)[0] + ".json"
        else:
            jsonfile = os.path.splitext(file)[0] + ".json"
        if not os.path.exists(jsonfile):
            log.warning(f"this file has no .json associated : {file}")
            file_list_nii.remove(file)
        else:
            file_list_json.append(jsonfile)

    log.info(f"remaining {len(file_list_nii)} nifti files")
    return file_list_nii, file_list_json


########################################################################################################################
@logit('Creation of internal object that will store all info, 1 per nifti.', logging.DEBUG)
def create_volume_list(file_list_nii: list[str]) -> list[Volume]:

    for file in file_list_nii:
        Volume(file)

    return Volume.instances


########################################################################################################################
@logit('Read all .json files. This step might take time, it involves reading lots of files', logging.INFO)
def read_all_json(volume_list: list[Volume]) -> None:

    for volume in volume_list:
        volume.load_json()


########################################################################################################################
@logit('Read nifti files header to store parameters that are not in the json', logging.INFO)
def read_all_nifti_header(volume_list: list[Volume]) -> None:

    for volume in volume_list:
        volume.load_header()


########################################################################################################################
def assemble_list_param_to_dataframe(volume_list: list[Volume]) -> pandas.DataFrame:

    list_param = []
    for volume in volume_list:
        list_param.append(volume.seqparam)

    return pandas.DataFrame(list_param)
