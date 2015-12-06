from flask import Blueprint, url_for, jsonify, abort, request
blueprint = Blueprint('api', __name__)

from octopus.core import app
from octopus.lib.getjsonreq import get_json
from octopus.lib.clcsv import get_csv_string
from service.lib import spreadsheetjob
from service import models, workflow

from uuid import uuid1


def job_progress(job):
    obj = spreadsheetjob.progress2json(job)
    obj['progress_url'] = app.config['SERVICE_BASE_URL'] + url_for('api.compliancejob_progress', job_id=job.id)
    obj['results_url'] = app.config['SERVICE_BASE_URL'] + url_for('download_progress_csv', job_id=job.id)

    return obj


@blueprint.route("/compliancejob", methods=['POST'])
def compliancejob_submit():
    if request.files:
        metadata = get_json(request, force=True, silent=True)
        webhook_callback = None
        if metadata and isinstance(metadata, dict) and "webhook_callback" in metadata:
            webhook_callback = metadata['webhook_callback']

        sheetf = request.files[0]

        job = workflow.csv_upload_a_file(sheetf, sheetf.filename, "null@example.org", webhook_callback=webhook_callback)
    else:
        j = get_json(request, force=True, silent=True)
        if not j:
            abort(400)
        if "articles" not in j:
            abort(400)
        thecsv = ''
        thecsv += get_csv_string(['DOI', 'PMID', 'PMCID', 'Title'])
        expected_metadata_keys = ['doi', 'pmid', 'pmcid', 'title']
        for a in j['articles']:
            if not isinstance(a, dict):
                continue
            if not list(set(a.keys()) & set(expected_metadata_keys)):  # if the article doesn't contain any expected data, ignore it
                continue
            thecsv += get_csv_string([a.get(k, '') for k in expected_metadata_keys])

        job = workflow.csv_upload_a_csvstring("api upload " + uuid1().hex, 'null@example.org', thecsv, webhook_callback=j.get('webhook_callback'))

    return jsonify(job_progress(job))


@blueprint.route("/compliancejob/progress/<job_id>", methods=['GET'])
def compliancejob_progress(job_id):
    job = models.SpreadsheetJob.pull(job_id)
    if not job:
        abort(404)
    return jsonify(job_progress(job))
