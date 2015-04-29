import json

from flask import Blueprint, url_for, jsonify, abort, redirect, request
blueprint = Blueprint('api', __name__)

from octopus.core import app
from octopus.lib.getjsonreq import get_json
from octopus.lib.clcsv import get_csv_string
from service.lib import spreadsheetjob
from service import models, workflow

from uuid import uuid1

@blueprint.route("/compliancejob", methods=['POST'])
def compliancejob_submit():
    if request.files:
        if not "sheet" in request.files:
            abort(400)

        metadataf = request.files.get("metadata")
        if metadataf:
            try:
                metadata = json.loads(metadataf.read())
            except ValueError:
                abort(400)
            webhook_callback = metadata.get('webhook_callback')
        else:
            webhook_callback = None

        sheetf = request.files["sheet"]

        job = workflow.csv_upload_a_file(sheetf, sheetf.filename, "null@example.org", webhook_callback=webhook_callback)
    else:
        j = get_json(request, force=True, silent=True)
        if not j:
            abort(400)
        if "articles" not in j:
            abort(400)
        thecsv = ''
        thecsv += get_csv_string(['DOI', 'PMID', 'PMCID', 'Title'])
        job = workflow.csv_upload_a_csvstring("api upload " + uuid1().hex, 'test@example.org', thecsv, webhook_callback=j.get('webhook_callback'))

    return redirect(url_for('api.compliancejob_progress', job_id=job.id))

@blueprint.route("/compliancejob/progress/<job_id>", methods=['GET'])
def compliancejob_progress(job_id):
    job = models.SpreadsheetJob.pull(job_id)
    if not job:
        abort(404)
    obj = spreadsheetjob.progress2json(job)
    obj['progress_url'] = app.config['SERVICE_BASE_URL'] + url_for('api.compliancejob_progress', job_id=job_id)
    obj['results_url'] = app.config['SERVICE_BASE_URL'] + url_for('download_progress_csv', job_id=job_id)

    return jsonify(obj)
