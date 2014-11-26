from octopus.core import app
from service import models, sheets
import codecs, os



class WorkflowException(Exception):
    pass

def csv_upload(flask_file_handle, filename, contact_email):
    # make a record of the upload
    s = models.SpreadsheetJob()

    s.filename = filename
    s.contact_email = contact_email
    s.status_code = "submitted"
    s.id = s.makeid()

    # find out where to put the file
    upload = app.config.get("UPLOAD_DIR")
    if upload is None or upload == "":
        raise WorkflowException("UPLOAD_DIR is not set")

    # save the file and the record of the upload
    flask_file_handle.save(os.path.join(upload, filename))
    s.save()

def normalise_pmcid(pmcid):
    return pmcid

def normalise_pmid(pmid):
    return pmid

def normalise_doi(doi):
    return doi

def parse_csv(job):
    # find out where to get the file
    upload = app.config.get("UPLOAD_DIR")
    if upload is None or upload == "":
        raise WorkflowException("UPLOAD_DIR is not set")

    path = os.path.join(upload, job.id + ".csv")
    sheet = sheets.MasterSheet(path)

    i = 0
    for obj in sheet.objects():
        i += 1
        r = models.Record()
        r.upload_id = job.id
        r.upload_pos = i
        r.set_source_data(**obj)

        if obj.get("pmcid") is not None and obj.get("pmcid") != "":
            r.pmcid = normalise_pmcid(obj.get("pmcid"))

        if obj.get("pmid") is not None and obj.get("pmid") != "":
            r.pmid = normalise_pmid(obj.get("pmid"))

        if obj.get("doi") is not None and obj.get("doi") != "":
            r.doi = normalise_doi(obj.get("doi"))

        if obj.get("article_title") is not None and obj.get("article_title") != "":
            r.title = obj.get("article_title")

        r.save()


