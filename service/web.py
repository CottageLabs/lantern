import subprocess
import argparse
import logging
import sys
import os
import json
from uuid import uuid1

from flask import Flask, request, abort, render_template, redirect, make_response, jsonify, send_file, \
    send_from_directory, url_for
from wtforms import Form, StringField, validators, SelectField
from wtforms.fields.html5 import EmailField
from werkzeug import secure_filename
from StringIO import StringIO

from service import models

from octopus.core import app, initialise
from octopus.lib.webapp import custom_static
from workflow import csv_upload_a_csvstring, csv_upload_a_file, email_submitter, output_csv
from octopus.lib.webapp import jsonp
from service.lib import spreadsheetjob
from octopus.lib.clcsv import get_csv_string

from service.view.api import blueprint as api
app.register_blueprint(api, url_prefix='/api')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config["ALLOWED_EXTENSIONS"]

class UploadForm(Form):
    contact_email = EmailField('Email Address', [validators.DataRequired(), validators.Email()])
    spreadsheet_type = SelectField('Type', choices=app.config.get('SPREADSHEET_OPTIONS'))


class DemoForm(Form):
    doi = StringField('DOI', [validators.Optional()])
    pmid = StringField('PMID', [validators.Optional()])
    pmcid = StringField('PMCID', [validators.Optional()])
    title = StringField('Title', [validators.Optional()])


@app.route("/", methods=['GET', 'POST'])
def root():  # do not rename this function - the octopus 404 page refers to "root" with url_for to get people back to a known area of the site
    form = UploadForm(request.form)
    invalid_file = False
    if request.method == "POST" and form.validate():
        file = request.files["upload"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            contact_email = form.contact_email.data
            job = csv_upload_a_file(file, filename, contact_email)
            url_root = request.url_root
            if url_root.endswith("/"):
                url_root = url_root[:-1]
            email_submitter(contact_email=contact_email, url=url_root + url_for('progress', job_id=job.id))
            return redirect(url_for('progress', job_id=job.id))
        else:
            invalid_file = True

    demoform = DemoForm()
    return render_template("upload_csv.html", form=form, demoform=demoform, invalid_file=invalid_file)

@app.route('/direct_demo_form', methods=['POST'])
def direct_demo_form():
    demoform = DemoForm(request.form)
    if demoform.validate():
        thecsv = ''
        thecsv += get_csv_string(['DOI', 'PMID', 'PMCID', 'Title'])
        if demoform.doi.data or demoform.pmid.data or demoform.pmcid.data or demoform.title.data:
            thecsv += get_csv_string([demoform.doi.data, demoform.pmid.data, demoform.pmcid.data, demoform.title.data])
            job = csv_upload_a_csvstring("demo form upload " + uuid1().hex, 'test@example.org', thecsv)  # /dev/null for emails
            return redirect(url_for('progress', job_id=job.id))

    form = UploadForm()
    invalid_file = False
    render_template("upload_csv.html", form=form, demoform=demoform, invalid_file=invalid_file)

@app.route("/docs")
def docs():
    return render_template("docs.html")

@app.route("/progress/<job_id>")
def progress(job_id):
    job = models.SpreadsheetJob.pull(job_id)
    return render_template("progress.html", filename=job.filename, job=job)

@app.route("/progress/<job_id>/pc")
def percentage(job_id):
    job = models.SpreadsheetJob.pull(job_id)
    pc = str(job.pc_complete)
    return pc

@app.route("/progress/<job_id>/status")
@jsonp
def status(job_id):
    job = models.SpreadsheetJob.pull(job_id)
    if not job:
        abort(404)
    obj = spreadsheetjob.progress2json(job)

    resp = make_response(json.dumps(obj))
    resp.mimetype = "application/json"
    return resp

"""
Use this to force certain states in the UI, and thus allow testing of different
statuses

@app.route("/progress/<job_id>/<test_type>")
@jsonp
def test_status(job_id, test_type):
    obj = {}

    if test_type == "submitted":
        obj = {
            "status" : "submitted",
            "pc" : 0.0,
            "queue" : "8"
        }
    elif test_type == "processing":
        import random
        obj = {
            "status" : "processing",
            "pc" : random.randint(0, 99) + random.random(),
            "queue" : "0"
        }
    elif test_type == "error":
        obj = {
            "status" : "error",
            "message" : "oops",
            "pc" : 0.0,
            "queue" : "0"
        }
    elif test_type == "complete":
        obj = {
            "status" : "complete",
            "pc" : 100.0,
            "queue" : "0"
        }

    resp = make_response(json.dumps(obj))
    resp.mimetype = "application/json"
    return resp
"""

@app.route("/download_original/<job_id>")
def download_original_csv(job_id):
    job = models.SpreadsheetJob.pull(job_id)
    original_name = job.filename
    filename = job_id + ".csv"
    return send_from_directory(os.path.abspath(app.config.get("UPLOAD_DIR")), filename, as_attachment=True, attachment_filename=original_name)

@app.route("/download_progress/<job_id>")
def download_progress_csv(job_id):
    job = models.SpreadsheetJob.pull(job_id)
    spreadsheet = output_csv(job)
    if type(spreadsheet) == unicode:
        spreadsheet = spreadsheet.encode('utf-8', 'ignore')
    filename = "processed_" + job.filename
    return send_file(StringIO(spreadsheet), attachment_filename=filename, as_attachment=True)


# health status endpoint
@app.route("/health")
def health():
    # if the request has come this far, the web app itself is fine so no
    # need to check

    # If there is an exception (e.g. *during* checks on the output of
    # commands), this web route will crash and burn. This is fine -
    # the Newrelic monitoring will get a 500 in response and we will be
    # alerted.

    oacwellcome_daemon_status = check_background_process("lantern-test-daemon")
    oagr_daemon_status = check_background_process("oagr-test-daemon")

    if not oacwellcome_daemon_status and not oagr_daemon_status:
        return "Both daemons have encountered a problem"

    if not oacwellcome_daemon_status:
        return "The OACWellcome Daemon has encountered a problem"

    if not oagr_daemon_status:
        return "The OAGR Daemon has encountered a problem"

    return "All OK"


def check_background_process(supervisord_process_name):
    output = subprocess.check_output(["sudo", "supervisorctl", "status", supervisord_process_name])

    if len(output.splitlines()) != 1:
        return "Wrong # of lines returned by supervisorctl for {0}, double check the command and correct the service.web.health code.".format(supervisord_process_name)

    if 'RUNNING' in output:
        return True

# this allows us to override the standard static file handling with our own dynamic version
@app.route("/static/<path:filename>")
def static(filename):
    return custom_static(filename)

# this allows us to serve our standard javascript config
from octopus.modules.clientjs.configjs import blueprint as configjs
app.register_blueprint(configjs)

# Autocomplete endpoint
from octopus.modules.es.autocomplete import blueprint as autocomplete
app.register_blueprint(autocomplete, url_prefix='/autocomplete')

# OAGR monitor endpoint
from octopus.modules.oag.monitor import blueprint as oagmonitor
app.register_blueprint(oagmonitor, url_prefix='/oagr')

# Query Endpoint
from octopus.modules.es.query import blueprint as query
app.register_blueprint(query, url_prefix="/query")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Lantern')
    parser.add_argument("--port", type=int, help="Port to start the app on. Default from settings: {0}".format(app.config['PORT']))
    parser.add_argument("-d", "--debug", action="store_true", help="Activate PyCharm debugging. Default from settings: {0}".format(app.config.get('DEBUG_PYCHARM', False)))
    parser.add_argument('--no-logging', dest='logging', action='store_false')
    parser.add_argument("--index", help="Elasticsearch index to use.")
    parser.set_defaults(port=app.config['PORT'], debug=app.config.get('DEBUG_PYCHARM', False), logging=True, index=app.config['ELASTIC_SEARCH_INDEX'])

    args = parser.parse_args(sys.argv[1:])

    pycharm_debug = args.debug
    port = args.port
    app.config['ELASTIC_SEARCH_INDEX'] = args.index  # need to override config when running as separate process for testing

    if pycharm_debug:
        app.config['DEBUG'] = False
        import pydevd
        pydevd.settrace(app.config.get('DEBUG_SERVER_HOST', 'localhost'), port=app.config.get('DEBUG_SERVER_PORT', 51234), stdoutToServer=True, stderrToServer=True)
        print "STARTED IN REMOTE DEBUG MODE"

    if not args.logging:
        logger = logging.getLogger('werkzeug')
        logger.setLevel(logging.ERROR)

    initialise()

    app.run(host='0.0.0.0', debug=app.config['DEBUG'], port=port, threaded=False)

