import flask           # html interface
import nifti2database  # ...
import json            # load, dump
import os              # join paths


# initialization of the app
dir_path = os.path.dirname(os.path.realpath(__file__))
app = flask.Flask('nifti2database',
                  template_folder=os.path.join(dir_path,'templates'))


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
    req = flask.request.get_data()
    print(req)
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
