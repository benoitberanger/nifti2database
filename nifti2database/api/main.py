# standard modules
import flask           # html interface
import json            # load, dump
import os              # join paths

# dependency modules
import niix2bids

# local modules
import nifti2database


# initialization of the app
dir_path = os.path.dirname(os.path.realpath(__file__))
app = flask.Flask('nifti2database',
                  template_folder=os.path.join(dir_path,'templates'))

# initialization of the logger
niix2bids.utils.init_logger(write_file=False, out_dir='',
                            store_report=True)  # this "report" is the output of the logger stored in a string


def render_string(string: str) -> str:
    return flask.render_template('display_string.html', string=string)


@app.route('/')
def index() -> str:
    return render_string("API is running")


@app.route('/help')
def get_help() -> str:
    parser = nifti2database.cli.get_parser()
    help_str = parser.format_help()
    return render_string(help_str)


@app.route('/nifti2database',methods=['POST'])
def run():

    req_dict = flask.request.get_json()

    if not req_dict:
        info = {
            'success': False,
            'input_request_dict': req_dict,
            'reason': 'empty JSON'
        }
        return json.dumps(info), 200, {'ContentType': 'application/json'}

    if 'args' not in req_dict:
        info = {
            'success': False,
            'input_request_dict': req_dict,
            'reason': '"args" key not in JSON'
        }
        return json.dumps(info), 200, {'ContentType': 'application/json'}

    if type(req_dict['args']) is not str:
        info = {
            'success': False,
            'input_request_dict': req_dict,
            'reason': '"args" is not a string'
        }
        return json.dumps(info), 200, {'ContentType': 'application/json'}

    args_list = req_dict['args'].split(' ')
    parser = nifti2database.cli.get_parser()
    try:
        args = parser.parse_args(args_list)
    except SystemExit:
        info = {
            'success': False,
            'input_request_dict': req_dict,
            'reason': '"args" => bad syntax',
            'usage': parser.format_usage(),
        }
        return json.dumps(info), 200, {'ContentType': 'application/json'}

    niix2bids.classes.Volume.instances = []  # we absolutely need to flush all instances

    report = ""
    success = False
    complete = False
    try :
        report = nifti2database.workflow.run(args=args, sysexit=False)
        success = True
        complete = 'Total execution time is' in report
    except:
        report = nifti2database.utils.get_report()

    info = {
        'success': success,
        'input_request_dict': req_dict,
        'input_args_list': args_list,
        'args': vars(args),
        'report': report,
    }
    return json.dumps(info), 200, {'ContentType': 'application/json'}
