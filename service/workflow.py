from octopus.core import app
from octopus.modules.epmc import client as epmc
from octopus.modules.doaj import client as doaj
from octopus.modules.identifiers import pmid, doi, pmcid
from octopus.lib import mail
from service import models, sheets, licences
import os, time
from StringIO import StringIO
from copy import deepcopy

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
    flask_file_handle.save(os.path.join(upload, s.id + ".csv"))
    s.save()

    # return the job that was created, in case the caller wants to do something with it
    return s

def email_submitter(contact_email, url):
    return mail.send_mail(to=[contact_email], subject="[oac] Successful upload", template_name="emails/upload_email_template.txt", url=url)


def normalise_pmcid(identifier):
    try:
        identifier = pmcid.normalise(identifier)
        return identifier
    except ValueError:
        return None

def normalise_pmid(identifier):
    try:
        identifier = pmid.normalise(identifier)
        return identifier
    except ValueError:
        return None

def normalise_doi(identifier):
    try:
        identifier = doi.normalise(identifier)
        return identifier
    except ValueError:
        return None

def parse_csv(job):
    app.logger.info("Loading records from " + job.id)

    # find out where to get the file
    upload = app.config.get("UPLOAD_DIR")
    if upload is None or upload == "":
        raise WorkflowException("UPLOAD_DIR is not set")

    path = os.path.join(upload, job.id + ".csv")

    # FIXME: what happens if the sheet can't be read
    sheet = sheets.MasterSheet(path)

    i = 0
    for obj in sheet.objects():
        i += 1
        r = models.Record()
        r.upload_id = job.id
        r.upload_pos = i
        r.set_source_data(**obj)

        # also copy the various identifiers over into the locations where they can be normalised
        # and used for lookup

        if obj.get("pmcid") is not None and obj.get("pmcid") != "":
            npmicd = normalise_pmcid(obj.get("pmcid"))
            if npmicd is not None:
                r.pmcid = npmicd
                note = "normalised PMCID %(source)s to %(target)s" % {"source" : obj.get("pmcid"), "target" : r.pmcid }
            else:
                note = "PMCID %(source)s was syntactically invalid, so ignoring" % {"source" : obj.get("pmcid")}

            r.add_provenance("importer", note)

        if obj.get("pmid") is not None and obj.get("pmid") != "":
            npmid = normalise_pmid(obj.get("pmid"))
            if npmid is not None:
                r.pmid = npmid
                note = "normalised PMID %(source)s to %(target)s" % {"source" : obj.get("pmid"), "target" : r.pmid }
            else:
                note = "PMID %(source)s was syntactically invalid, so ignoring" % {"source" : obj.get("pmid")}
            r.add_provenance("importer", note)

        if obj.get("doi") is not None and obj.get("doi") != "":
            ndoi = normalise_doi(obj.get("doi"))
            if ndoi is not None:
                r.doi = ndoi
                note = "normalised DOI %(source)s to %(target)s" % {"source" : obj.get("doi"), "target" : r.doi }
            else:
                note = "DOI %(source)s was syntactically invalid, so ignoring" % {"source" : obj.get("doi")}
            r.add_provenance("importer", note)

        if obj.get("article_title") is not None and obj.get("article_title") != "":
            r.title = obj.get("article_title")

        r.save()

    app.logger.info("Loaded " + str(i) + " records from spreadsheet")

    # refresh the index so the data is ready to use
    models.Record.refresh()

def output_csv(job):
    def serialise_provenance(r):
        s = ""
        first = True
        for by, when, what in r.provenance:
            if not first:
                s += "\n\n"
            else:
                first = False
            s += "[%(when)s %(by)s] %(what)s" % {"when" : when, "by" : by, "what" : what}
        return s

    def objectify(r):
        obj = {
            # the identifiers
            "pmcid" : r.pmcid,
            "pmid" : r.pmid,
            "doi" : r.doi,
            "article_title" : r.title,

            # the results of the run
            "in_epmc" : r.in_epmc,
            "xml_ft_in_epmc" : r.has_ft_xml,
            "aam" : r.aam,
            "open_access" : r.is_oa,
            "licence" : r.licence_type,
            "licence_source" : r.licence_source,
            "journal_type" : r.journal_type,
            "confidence" : r.confidence,
            "standard_compliance" : r.standard_compliance,
            "deluxe_compliance" : r.deluxe_compliance,
            "notes" : serialise_provenance(r),
            "issn" : ", ".join(r.issn)
        }

        # add the original data if present
        if r.source is not None:
            original = deepcopy(r.source)
            if "pmcid" in original:
                del original["pmcid"]
            if "pmid" in original:
                del original["pmid"]
            if "doi" in original:
                del original["doi"]
            if "article_title" in original:
                del original["article_title"]
            obj.update(original)

        return obj

    # get the records and work out what shape they are
    # (makes the assumption that all records have the same spec, which /should/ be true)
    records = models.Record.list_by_upload(job.id)
    spec = objectify(records[0])

    # create a master spreadsheet with the right shape
    s = StringIO()
    sheet = sheets.MasterSheet(writer=s, spec=spec.keys())

    # for each record, objectify it and add to the sheet
    for r in records:
        assert isinstance(r, models.Record)
        obj = objectify(r)
        sheet.add_object(obj)

    sheet.save()

    return s.getvalue()

class WorkflowMessage(object):
    def __init__(self, job=None, record=None, oag_register=None):
        self.job = job
        self.record = record
        self.oag_register = oag_register

def process_jobs():
    """
    Process all of the jobs in the index which are of status "submitted"
    :return:nothing
    """
    app.logger.debug("Processing spreadsheet jobs")
    jobs = models.SpreadsheetJob.list_by_status("submitted")
    for job in jobs:
        process_job(job)
    app.logger.debug("Processing run complete")

def process_job(job):
    """
    Process the spreadsheet job in its entirety

    :param job: models.SpreadsheetJob object
    :return:    nothing
    """

    app.logger.info("Processing spreadsheet job " + job.id)

    # start by switching the status of the job so it is active
    job.status_code = "processing"
    job.save()

    # now we want to parse the csv itself to our record index
    parse_csv(job)

    # list all of the records, and work through them one by one doing all the processing
    records = models.Record.list_by_upload(job.id)
    oag_register = []
    for record in records:
        msg = WorkflowMessage(job, record, oag_register)
        process_record(msg)

    # the oag_register will now contain all the records that need to go on to OAG
    process_oag(oag_register, job)

    # beyond this point all the processing is handled asynchronously, so this function
    # is now complete
    app.logger.info("Processing spreadsheet " + job.id + " complete")

def process_record(msg):
    """
    Process an individual record (as represented by the workflow message)

    :param msg:  WorkflowMessage object containing the record to process
    :return:
    """

    app.logger.info("Processing record " + msg.record.id)

    # get the epmc metadata for this record
    epmc_md, confidence = get_epmc_md(msg)
    if epmc_md is None:
        # if no metadata, then we have to give up
        note = "unable to locate any metadata record in EPMC for the combination of identifiers/title; giving up"
        msg.record.add_provenance("processor", note)
        msg.record.epmc_complete = True
        msg.record.oag_complete = True
        msg.record.save()
        return

    # set the confidence that we have accurately identified this record
    msg.record.confidence = confidence

    # populate the missing identifiers
    populate_identifiers(msg, epmc_md)

    # add the key bits of metadata we're interested in
    extract_metadata(msg, epmc_md)

    # now we've extracted all we can from the EPMC metadata, let's save before moving on to the
    # next external request
    msg.record.save()

    # obtain the fulltext, and if found, extract metadata and licence information from it
    fulltext = get_epmc_fulltext(msg)
    if fulltext is not None:
        extract_fulltext_info(msg, fulltext)
        extract_fulltext_licence(msg, fulltext)

        # since we have extracted data, and are about to do another external request, save again
        msg.record.save()
    else:
        msg.record.has_ft_xml = False

    # lookup the issn in the DOAJ, and record whether the journal is OA or hybrid
    hybrid_or_oa(msg)

    # at this stage, all the epmc lookup work has completed
    msg.record.epmc_complete = True

    # if necessary, register an identifier to be looked up in OAG
    register_with_oag(msg)

    # finally, save the record in its current state, which is as far as we can go with it
    msg.record.save()

    # after this, all additional work will be picked up by the OAG processing chain, asynchronously
    app.logger.info("Record processed")

def process_oag(oag_register, job):
    app.logger.info("Running " + str(len(oag_register)) + " identifiers through OAG")

    from octopus.modules.oag import client, oagr
    from datetime import datetime, timedelta

    # first create and set going the oagrjob after a short delay
    # FIXME: note that OAGR doesn't work with the id type - will this be a problem later?
    req = client.RequestState([o.get("id") for o in oag_register], start=datetime.now() + timedelta(seconds=10))
    oagrjob = oagr.JobRunner.make_job(req)

    # now create a link between the spreadsheet job and the oagr job
    oagrlink = models.OAGRLink()
    oagrlink.oagrjob_id = oagrjob.id
    oagrlink.spreadsheet_id = job.id
    oagrlink.save()

    # and that's all we can do from here - the OAGR system will run our callback on any data it gets back, you can find
    # that defined at the bottom of this file and in the OAGR_RUNNER_CALLBACK_CLOSURE config option

def process_oag_direct(oag_register, job):

    app.logger.info("Running " + str(len(oag_register)) + " identifiers through OAG")

    # delayed imports because this function is a prototype and we'll wholesale replace it in the full service
    import json, requests
    postdata = json.dumps(oag_register)
    resp = requests.post("http://howopenisit.org/lookup", postdata)
    licences = json.loads(resp.text)

    # in the full service there will be a single callback that will take the OAGR state object and
    # extract the successes and errors - this is just a stand in, and oag_record_callback is where we will
    # initially put all the callback functionality.
    oag_rerun = []
    for r in licences.get("results", []):
        oag_record_callback(r, oag_rerun)
    for e in licences.get("errors", []):
        oag_record_callback(e, oag_rerun)

    # refresh the index, since this code moves faster than it can refresh itself
    models.Record.refresh()

    # FIXME: in the full service, this is next bit is no good.  We will instead need to query the index
    # and determine if all the records are complete.  This might involve marking the records as complete
    # at some stage.

    # at this stage we now have a list of new identifiers which need to be re-run (or an empty list)
    if len(oag_rerun) == 0:
        job.status_code = "complete"
        job.save()
    else:
        # FIXME: note that this could result in exceeding the maximum stack depth if we aren't careful.
        # the full service won't be allowed to behave like this
        process_oag(oag_rerun, job)


def get_epmc_md(msg):
    # look using the pmcid first
    if msg.record.pmcid is not None:
        app.logger.info("Requesting EPMC metadata by PMCID " + msg.record.pmcid)
        try:
            mds = epmc.EuropePMC.get_by_pmcid(msg.record.pmcid)
            if len(mds) == 1:
                app.logger.info("EPMC metadata found")
                return mds[0], 1.0
        except epmc.EuropePMCException:
            # just try the next one
            pass

    # if we find 0 or > 1 via the pmcid, try again with the pmid
    if msg.record.pmid is not None:
        app.logger.info("Requesting EPMC metadata by PMID " + msg.record.pmid)
        try:
            mds = epmc.EuropePMC.get_by_pmid(msg.record.pmid)
            if len(mds) == 1:
                app.logger.info("EPMC metadata found")
                return mds[0], 1.0
        except epmc.EuropePMCException:
            # just try the next one
            pass

    # if we find 0 or > 1 via the pmid, try again with the doi
    if msg.record.doi is not None:
        app.logger.info("Requesting EPMC metadata by DOI " + msg.record.doi)
        try:
            mds = epmc.EuropePMC.get_by_doi(msg.record.doi)
            if len(mds) == 1:
                app.logger.info("EPMC metadata found")
                return mds[0], 1.0
        except epmc.EuropePMCException:
            # just try the next one
            pass

    if msg.record.title is not None:
        app.logger.info("Requesting EPMC metadata by exact Title " + msg.record.title)
        try:
            mds = epmc.EuropePMC.title_exact(msg.record.title)
            if len(mds) == 1:
                app.logger.info("EPMC metadata found")
                return mds[0], 0.9
        except epmc.EuropePMCException:
            # just try the next one
            pass

        app.logger.info("Requesting EPMC metadata by fuzzy Title " + msg.record.title)
        try:
            mds = epmc.EuropePMC.title_approximate(msg.record.title)
            if len(mds) == 1:
                app.logger.info("EPMC metadata found")
                return mds[0], 0.7
        except epmc.EuropePMCException:
            # oh well, we did our best
            pass

    app.logger.info("EPMC metadata not found by any means available")
    return None, None


def register_with_oag(msg):
    # if we have a pmcid, then we register it for lookup if the licence is missing OR if the AAM information
    # has not been retrieved yet
    if msg.record.pmcid is not None:
        if msg.record.aam_from_xml and msg.record.licence_type is not None:
            app.logger.info("No need to process record with OAG " + msg.record.id)
            msg.record.oag_complete = True
            return
        else:
            app.logger.info("Sending PMCID " + msg.record.pmcid + " to OAG for record " + msg.record.id)
            msg.oag_register.append({"id" : msg.record.pmcid, "type" : "pmcid"})
            msg.record.in_oag = True
            msg.record.oag_pmcid = "sent"
            msg.record.save()
            return

    # in all other cases, if the licence has already been detected, we don't need to do any more
    if msg.record.licence_type is not None:
        app.logger.info("No need to process record with OAG " + msg.record.id)
        msg.record.oag_complete = True
        return

    # next priority is to send a doi if there is one
    if msg.record.doi is not None:
        app.logger.info("Sending DOI " + msg.record.doi + " to OAG for record " + msg.record.id)
        msg.oag_register.append({"id" : msg.record.doi, "type" : "doi"})
        msg.record.in_oag = True
        msg.record.oag_doi = "sent"
        msg.record.save()
        return

    # lowest priority is to send the pmid if there is one
    if msg.record.pmid is not None:
        app.logger.info("Sending PMID " + msg.record.pmid + " to OAG for record " + msg.record.id)
        msg.oag_register.append({"id" : msg.record.pmid, "type" : "pmid"})
        msg.record.in_oag = True
        msg.record.oag_pmid = "sent"
        msg.record.save()
        return

    # if we get to here, then something is wrong with this record, and we can't send it to OAG
    app.logger.info("No need to process record with OAG " + msg.record.id)
    msg.record.oag_complete = True
    return


def get_epmc_fulltext(msg):
    """
    Get the fulltext record if it exists
    :param msg: WorkflowMessage object
    :return: EPMCFulltext object or None if not found
    """
    app.logger.info("Looking for EPMC fulltext for " + str(msg.record.id))

    if msg.record.pmcid is None:
        app.logger.info("Fulltext not available")
        return None

    try:
        ft = epmc.EuropePMC.fulltext(msg.record.pmcid)
        app.logger.info("Fulltext found for " + str(msg.record.id))
        return ft
    except epmc.EuropePMCException:
        app.logger.info("Fulltext not available")
        return None

def doaj_lookup(msg):
    """
    Lookup the issn in the record in the DOAJ.  If we find it, this means the journal
    is pure OA

    :param msg: WorkflowMessage object
    :return:    True if the journal is OA, False if hybrid
    """
    app.logger.info("Looking up record in DOAJ " + str(msg.record.id))
    client = doaj.DOAJSearchClient()
    journals = client.journals_by_issns(msg.record.issn)
    return len(journals) > 0

def hybrid_or_oa(msg):
    oajournal = doaj_lookup(msg)
    msg.record.journal_type = "oa" if oajournal else "hybrid"
    if oajournal:
        msg.record.add_provenance("processor", "Journal with ISSN %(issn)s was found in DOAJ; assuming OA" % {"issn" : ",".join(msg.record.issn)})
    else:
        msg.record.add_provenance("processor", "Journal with ISSN %(issn)s was not found in DOAJ; assuming Hybrid" % {"issn" : ",".join(msg.record.issn)})

def populate_identifiers(msg, epmc_md):
    """
    Any identifiers which are present in the EPMC metadata but not in the source
    record should be copied over.

    Note that this does not check identifiers which are present in both sources for
    discrepencies.  It is assumed that the record in the WorkflowMessage is definitive

    :param msg:     WorkflowMessage object
    :param epmc_md:     EPMC metadata object
    :return:
    """
    if msg.record.pmcid is None and epmc_md.pmcid is not None:
        msg.record.pmcid = normalise_pmcid(epmc_md.pmcid)

    if msg.record.pmid is None and epmc_md.pmid is not None:
        msg.record.pmid = normalise_pmid(epmc_md.pmid)

    if msg.record.doi is None and epmc_md.doi is not None:
        msg.record.doi = normalise_doi(epmc_md.doi)

def extract_metadata(msg, epmc_md):
    """
    Extract the inEPMC and isOA properties of the metadata

    :param msg: WorkflowMessage object
    :param epmc_md: EPMC Metadata object
    :return:
    """
    if epmc_md.in_epmc is not None:
        msg.record.in_epmc = epmc_md.in_epmc == "Y"

    if epmc_md.is_oa is not None:
        msg.record.is_oa = epmc_md.is_oa == "Y"

    if epmc_md.issn is not None:
        msg.record.add_issn(epmc_md.issn)
    if epmc_md.essn is not None:
        msg.record.add_issn(epmc_md.essn)

def extract_fulltext_info(msg, fulltext):
    # record that the fulltext exists in the first place
    msg.record.has_ft_xml = True
    msg.record.add_provenance("processor", "Found fulltext XML in EPMC")

    # record whether the fulltext tells us this is an author manuscript
    msg.record.aam = fulltext.is_aam
    msg.record.aam_from_xml = True

def extract_fulltext_licence(msg, fulltext):
    type, url, para = fulltext.get_licence_details()

    if type is not None and type in [l for u, l in licences.urls]:
        msg.record.licence_type = type
        msg.record.add_provenance("processor", "Fulltext XML specifies licence type as %(license)s" % {"license" : type})
        msg.record.licence_source = "epmc_xml"
        return

    if url is not None:
        urls = [u for u, l in licences.urls]
        for u in urls:
            if url.startswith(u):
                msg.record.licence_type = [l for u2, l in licences.urls if u == u2][0]
                msg.record.add_provenance("processor", "Fulltext XML specifies licence url as %(url)s which gives us licence type %(license)s" % {"url" : url, "license" : msg.record.licence_type})
                msg.record.licence_source = "epmc_xml"
                return

    if para is not None:
        for ss, t in licences.substrings:
            if ss in para:
                msg.record.licence_type = t
                msg.record.add_provenance("processor", "Fulltext XML licence description contains the licence text %(text)s which gives us licence type %(license)s" % {"text" : ss, "license" : t})
                msg.record.licence_source = "epmc_xml"
                break

def add_to_rerun(record, idtype, oag_rerun):
    if idtype == "pmcid":
        if record.doi is not None:
            oag_rerun.append({"id" : record.doi, "type" : "doi"})
            return True
        if record.pmid is not None:
            oag_rerun.append({"id" : record.pmid, "type" : "pmid"})
            return True
        return False
    elif idtype == "doi":
        if record.pmid is not None:
            oag_rerun.append({"id" : record.pmid, "type" : "pmid"})
            return True
        return False
    elif idtype == "pmid":
        return False

#################################################################

def oag_callback_closure():
    def oag_callback(state):
        # a register of identifiers which need to be re-run
        oag_rerun = []

        # follow the link over to the related spreadsheet
        oagrlink = models.OAGRLink.by_oagr_id(state.id)
        ssjob = models.SpreadsheetJob.pull(oagrlink.spreadsheet_id)

        # handle the successes
        successes = state.flush_success()
        for s in successes:
            oag_record_callback(s, oag_rerun, ssjob)

        # handle the errors
        errors = state.flush_error()
        for e in errors:
            oag_record_callback(e, oag_rerun, ssjob)

        # if there is anything to reprocess, do that
        if len(oag_rerun) > 0:
            # put anything that needs to be reprocessed back on the job queue
            process_oag(oag_rerun, ssjob)

        else:
            # it's possible that the spreadsheet job has finished, so we need
            # to check and update if so
            time.sleep(2)   # just to give the index a bit of time to refresh
            pc = ssjob.pc_complete
            if int(pc) == 100:
                ssjob.status_code = "complete"
                ssjob.save()
                send_complete_mail(ssjob)

    return oag_callback

def send_complete_mail(job):
    from flask import url_for
    url_root = app.config.get("SERVICE_BASE_URL")

    try:
        url = url_root + url_for("progress", job_id=job.id)
    except:
        from service.web import app as a2
        ctx = a2.test_request_context()
        ctx.push()
        url = url_root + url_for("progress", job_id=job.id)
        ctx.pop()

    mail.send_mail(to=[job.contact_email], subject="[oac] Processing complete", template_name="emails/complete_email_template.txt", url=url)

def oag_record_callback(result, oag_rerun, ssjob):

    def handle_error(record, idtype, error_message, oag_rerun):
        # first record an error status against the id type
        if idtype == "pmcid":
            record.oag_pmcid = "error"
        elif idtype == "pmid":
            record.oag_pmid = "error"
        elif idtype == "doi":
            record.oag_doi = "error"

        record.add_provenance("oag", error_message)

        # save the record then pass it on to see if it needs to be re-submitted
        added = add_to_rerun(record, idtype, oag_rerun)
        if not added:
            record.oag_complete = True
        record.save()

    def handle_fto(record, idtype, oag_rerun):
        # first record an error status against the id type
        if idtype == "pmcid":
            record.oag_pmcid = "fto"
        elif idtype == "pmid":
            record.oag_pmid = "fto"
        elif idtype == "doi":
            record.oag_doi = "fto"

        # save the record then pass it on to see if it needs to be re-submitted
        added = add_to_rerun(record, idtype, oag_rerun)
        if not added:
            record.oag_complete = True
        record.save()

    def handle_success(result, record, idtype):
        # first record an error status against the id type
        if idtype == "pmcid":
            record.oag_pmcid = "success"
            record.licence_source = "epmc"
        elif idtype == "pmid":
            record.oag_pmid = "success"
            record.licence_source = "publisher"
        elif idtype == "doi":
            record.oag_doi = "success"
            record.licence_source = "publisher"

        record.licence_type = result.get("license", [{}])[0].get("type")
        record.oag_complete = True
        record.save()
        return

    def handle_aam(result, record):
        aam = result.get("license", [{}])[0].get("provenance", {}).get("accepted_author_manuscript")
        if aam is not None:
            record.aam = aam
            record.aam_from_epmc = True
            record.add_provenance("oag", "Detected AAM status from EPMC web page")

    def process_licence(result, record, idtype, oag_rerun):
        # if the record already has a licence, we don't do anything
        if record.licence_type is not None:
            record.oag_complete = True
            record.save()
            return

        # get the OAG provenance description and put it into the record
        prov = result.get("license", [{}])[0].get("provenance", {}).get("description")
        record.add_provenance("oag", prov)

        if result.get("license", [{}])[0].get("type") == "failed-to-obtain-license":
            handle_fto(record, idtype, oag_rerun)
        else:
            handle_success(result, record, idtype)

    iserror = False

    # start by getting the identifier of the object that has been processed
    ident = result.get("identifier")
    if isinstance(ident, list):
        id = ident[0].get("id")
        type = ident[0].get("type")
    else:
        iserror = True
        id = ident.get("id")
        type = ident.get("type")

    # if there's no id, there's nothing we can do
    if id is None:
        app.logger.info("insufficient data to relate OAG response to record: no ID")
        return

    # OAG may represent pmcid as epmc as an identifier type
    if type == "epmc":
        type = "pmcid"

    # try to get a record from the id, job id, and type
    record = models.Record.get_by_identifier(id, ssjob.id, type)

    # if we didn't find a unique record, we can't do anything
    if record is None:
        app.logger.info("was unable to relate OAG response to record")
        return

    assert isinstance(record, models.Record)    # For pycharm type inspection

    app.logger.info("handling OAG response for " + id)

    # set its in_oag flag and re-save it
    record.in_oag = False
    record.save()

    # by this point we must know the type
    if type is None:
        if id == record.pmcid:
            type = "pmcid"
        elif id == record.pmid:
            type = "pmid"
        elif id == record.doi:
            type = "doi"
        else:
            app.logger.info("unable to determine the type for " + str(id))

    if type == "pmcid":
        if iserror:
            handle_error(record, "pmcid", result.get("error"), oag_rerun)
            return
        else:
            if not record.aam_from_xml:
                handle_aam(result, record)
            process_licence(result, record, type, oag_rerun)
    elif type == "doi":
        if iserror:
            handle_error(record, "doi", result.get("error"), oag_rerun)
            return
        else:
            process_licence(result, record, type, oag_rerun)
    elif type == "pmid":
        if iserror:
            handle_error(record, "pmid", result.get("error"), oag_rerun)
        else:
            process_licence(result, record, type, oag_rerun)
    else:
        app.logger.info("type of id was not one of pmcid, doi, pmid")





