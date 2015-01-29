from flask import Flask, request, abort, render_template, redirect, make_response, jsonify, send_file, \
    send_from_directory, url_for
from flask.views import View
from wtforms import Form, StringField, validators, SelectField
from wtforms.fields.html5 import EmailField
from werkzeug import secure_filename
from datetime import datetime
from StringIO import StringIO
import os

from service import models

from octopus.core import app, initialise
from octopus.lib.webapp import custom_static
from workflow import csv_upload, email_submitter, output_csv

import sys


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config["ALLOWED_EXTENSIONS"]

class UploadForm(Form):
    contact_email = EmailField('Email Address', [validators.DataRequired(), validators.Email()])
    spreadsheet_type = SelectField('Type', choices=app.config.get('SPREADSHEET_OPTIONS'))


@app.route("/", methods=['GET', 'POST'])
#@app.route("/upload_csv", methods=['GET', 'POST'])
def upload_csv():
    form = UploadForm(request.form)
    invalid_file = False
    if request.method == "POST" and form.validate():
        file = request.files["upload"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            contact_email = form.contact_email.data
            job = csv_upload(file, filename, contact_email)
            url_root = request.url_root
            if url_root.endswith("/"):
                url_root = url_root[:-1]
            email_submitter(contact_email=contact_email, url=url_root + url_for('progress', job_id=job.id))
            return redirect(url_for('progress', job_id=job.id))
        else:
            invalid_file = True
    return render_template("upload_csv.html", form=form, invalid_file=invalid_file)

@app.route("/progress/<job_id>")
def progress(job_id):
    job = models.SpreadsheetJob.pull(job_id)
    return render_template("progress.html", filename=job.filename, job=job)

@app.route("/progress/<job_id>/pc")
def percentage(job_id):
    job = models.SpreadsheetJob.pull(job_id)
    pc = str(job.pc_complete)
    return pc

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
    pycharm_debug = app.config.get('DEBUG_PYCHARM', False)
    if len(sys.argv) > 1:
        if sys.argv[1] == '-d':
            pycharm_debug = True

    if pycharm_debug:
        app.config['DEBUG'] = False
        import pydevd
        pydevd.settrace(app.config.get('DEBUG_SERVER_HOST', 'localhost'), port=app.config.get('DEBUG_SERVER_PORT', 51234), stdoutToServer=True, stderrToServer=True)
        print "STARTED IN REMOTE DEBUG MODE"

    initialise()
    app.run(host='0.0.0.0', debug=app.config['DEBUG'], port=app.config['PORT'], threaded=False)
    # app.run(host=app.config.get("HOST", "0.0.0.0"), debug=app.config.get("DEBUG", False), port=app.config.get("PORT", 5000), threaded=True)
    # start_from_main(app)

