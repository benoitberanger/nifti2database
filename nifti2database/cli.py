# standard modules
import argparse  # parser of the CLI
import os        # for path management

# dependency modules
import niix2bids

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
    if args.out_dir:
        args.out_dir = os.path.abspath(args.out_dir)

    # credentials
    args.credentials = os.path.abspath(args.credentials)

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

    optional.add_argument("-o", "--out_dir",
                          help="Output directory, receiving the log file.",
                          metavar='DIR',
                          required=False)

    exclusive1 = optional.add_mutually_exclusive_group()
    exclusive1.add_argument("--connect",
                            help="Use psycopg2.connect() to execute SQL 'INSERT' request (default)",
                            dest="connect_or_prepare",
                            action="store_const",
                            const="connect")
    exclusive1.add_argument("--prepare",
                            help="Do not connect and write all SQL 'INSERT' lines in an output file",
                            dest="connect_or_prepare",
                            action="store_const",
                            const="prepare")
    exclusive1.set_defaults(connect_or_prepare="connect")

    optional.add_argument("--config_file",
                          help=(
                              "If you want to use non-coded sequences such as new Products, WIP or C2P,\n"
                              "you can provide a config file.\n"
                              "Default location is ~/niix2bids_config_file/siemens.py\n"
                              "If default location is not present, try to use the template file \n"
                              "located in [niix2bids]/config_file/siemens.py"
                          ),
                          dest="config_file",
                          metavar='FILE',
                          default=[
                              os.path.join( os.path.expanduser('~'), 'niix2bids_config_file', 'siemens.py'),
                              os.path.join( niix2bids.__path__[0], 'config_file', 'siemens.py')
                          ]
                          )

    optional.add_argument("--credentials",
                          help=(
                              "[nifti2database] will by default look for a credential json files \n"
                              "located here : ~/credentials_nifti2database.json \n"
                              "Otherwise, the user can provide it's path using this argument \n"
                              "The file should lool like this :  \n"
                              '{ \n'
                              '    "user": "username", \n'
                              '    "password": "********", \n'
                              '    "database": "mydatabase", \n'
                              '    "host": "ip_adress/host_name", \n'
                              '    "port": "5432", \n'
                              '    "schema: "myschema", \n'
                              '    "table: "mytable" \n'
                              '   ["sslmode": "disable"] \n'
                              '   ["gssencmode": "disable"] \n'
                              '} \n'
                              "!!! fields in [brackets] are optional, it depends on the server config \n"
                              "\n"

                          ),
                          dest="credentials",
                          metavar='FILE',
                          default=os.path.join( os.path.expanduser('~'), 'credentials_nifti2database.json' )
                          )

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
