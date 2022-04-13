# standard modules
import argparse  # parser of the CLI
import os        # for path management

# dependency modules

# local modules
import nifti2database
from nifti2database import metadata


########################################################################################################################
def format_args(args: argparse.Namespace) -> argparse.Namespace:

    # in
    if isinstance(args.in_dir, str): # force single str to be list, for easier management
        args.in_dir = [args.in_dir]
    if isinstance(args.in_dir, list) and len(args.in_dir)==1 and isinstance(args.in_dir[0], list): # usually from debugging, when using a script
        args.in_dir = args.in_dir[0]
    args.in_dir = [os.path.abspath(one_dir) for one_dir in args.in_dir]

    # out
    args.out_dir = '/tmp/'

    return args


########################################################################################################################
def get_parser() -> argparse.ArgumentParser:

    nifti2database_version = metadata.get_nifti2database_version()

    description = """
    Parse nifti and json sidecare paramters and export them into a database for easy query.
    """

    epilog = f"nifti2database version = {nifti2database_version}"

    # Parse command line arguments
    parser = argparse.ArgumentParser(description=description,
                                     epilog=epilog,
                                     formatter_class=argparse.RawTextHelpFormatter)

    # This is a strategy found on stackoverflow to separate 'Required arguments' and 'Optional arguments'
    # in a way --help display looks more readable
    optional = parser._action_groups.pop()  # extract optional arguments
    optional.title = "Optional arguments"

    # and now we add 'Required arguments'
    required = parser.add_argument_group("Required arguments")

    required.add_argument("-i", "--in_dir",
                          help=(
                              "Nifti directories that will be parsed.\n"
                              "This directory is usually in xnat/archive.\n"
                              "This argument accepts several paths. You can use syntax such as /path/to/nii/2021_*"
                          ),
                          nargs='+',
                          metavar='DIR',
                          required=True)

    optional.add_argument("--logfile",
                          help="Write logfile",
                          dest="logfile",
                          action="store_true")
    optional.add_argument("--no-logfile",
                          help="Disable writing logfile (default)",
                          dest="logfile",
                          action="store_false")
    optional.set_defaults(logfile=False)

    optional.add_argument("-v", "--version",
                          action="version",
                          version=nifti2database_version)

    parser._action_groups.append(optional)  # this trick is just so the --help option appears correctly

    return parser


########################################################################################################################
def main() -> None:

    # Parse inputs
    parser = get_parser()       # Fetch my parser
    args = parser.parse_args()  # Parse
    args = format_args(args)    # Format args

    # Call workflow
    nifti2database.workflow.run(args)
