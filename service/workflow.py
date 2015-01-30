from octopus.core import app
from octopus.modules.epmc import client as epmc
from octopus.modules.doaj import client as doaj
from octopus.modules.identifiers import pmid, doi, pmcid
from octopus.lib import mail
from service import models, sheets, licences
import os, time, traceback
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

    # FIXME: I'm not totally convinced this a/ works or b/ is a good idea
    # Refresh can behave quite strangely, sometimes,
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
            "provenance" : serialise_provenance(r),
            "issn" : ", ".join(r.issn),

            # this is also a result of the run, but it can be overridden by the source data
            # if it was passed in and not empty
            "journal_title" : r.journal
        }

        # add the original data if present, being careful not to overwrite the data we have produced
        if r.source is not None:
            # list the fields to overwrite in the source.  Note that journal_title should only be overwritten
            # if the source does not contain a value
            overwrite = obj.keys()
            jt = r.source.get("journal_title")
            if jt is not None and jt != "":
                overwrite.remove("journal_title")

            original = deepcopy(r.source)
            for k in overwrite:
                if k in original:
                    del original[k]
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

    try:
        app.logger.info("Processing spreadsheet job " + job.id)

        job.status_code = "processing"
        job.save()

        # now we want to parse the csv itself to our record index
        try:
            parse_csv(job)
        except Exception:
            thetraceback = traceback.format_exc()
            app.logger.error("Trouble with parsing CSV {0}.csv for job {0}".format(job.id) + "\n\n" + thetraceback)
            job.set_status(u'error', thetraceback)
            return

        # list all of the records, and work through them one by one doing all the processing
        records = models.Record.list_by_upload(job.id)
        oag_register = []
        for record in records:
            msg = WorkflowMessage(job, record, oag_register)
            try:
                process_record(msg)
            except Exception:
                app.logger.error("Problem while processing record id {0}".format(record.id) + "\n\n" + traceback.format_exc())

        # FIXME: the last record is saved at the end of process_record, and then we go straight
        # into a duplicate check, which may overwrite the record.  We should therefore refresh,
        # wait, or perhaps better have the duplicates build up during the above process, so that
        # we already know about them.  For the time being, including a time.sleep here as a weak
        # stop-gap
        time.sleep(2)

        # at this point we have fleshed out all possible identifiers, so we need to check
        # for duplicates
        try:
            duplicate_check(job)
        except Exception:
            app.logger.error("Problem while detecting duplicates in job {0}".format(job.id) + "\n\n" + traceback.format_exc())

        # FIXME: duplicate check saves changes to records which may subsequently get picked up by OAG.
        # Further down, OAG delays its start, but this is all a weak stop-gap.  Put in a time.sleep
        # for the moment, but bear in mind we need a better long-term solution
        time.sleep(2)

        # the oag_register will now contain all the records that need to go on to OAG
        try:
            process_oag(oag_register, job)
        except Exception:
            app.logger.error("Problem while creating OAGR jobs for OACWellcome job id {0}".format(job.id) + "\n\n" + traceback.format_exc())
            return

        # beyond this point all the processing is handled asynchronously, so this function
        # is now complete
        app.logger.info("Processing spreadsheet " + job.id + " complete")

    except Exception:
        app.logger.error("Unknown problem while processing job {0}".format(job.id) + "\n\n" + traceback.format_exc())
        return

def process_record(msg):
    """
    Process an individual record (as represented by the workflow message)

    :param msg:  WorkflowMessage object containing the record to process
    :return:
    """

    app.logger.info("Processing record " + str(msg.record.id))

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
    # msg.record.save()

    # obtain the fulltext, and if found, extract metadata and licence information from it
    fulltext = get_epmc_fulltext(msg)
    if fulltext is not None:
        extract_fulltext_info(msg, fulltext)
        extract_fulltext_licence(msg, fulltext)

        # since we have extracted data, and are about to do another external request, save again
        # msg.record.save()
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

def duplicate_check(job):
    dupes = job.list_duplicate_identifiers()

    dupemsg = "This record's {type} is a duplicate of another in the same upload.  Compliance results should therefore be reviewed carefully, in case this indicates an erroneous set of identifiers"

    inmem = {}

    app.logger.info("Found the following duplicates in job {x}: {pmc} PMCIDs, {pmid} PMIDs, {doi} DOIs".format(
        x=job.id,
        pmc=len(dupes.get("pmcid", [])),
        pmid=len(dupes.get("pmid", [])),
        doi=len(dupes.get("doi", []))
    ))

    for id in dupes.get("pmcid", []):
        matches = models.Record.get_by_identifier(id, job.id, "pmcid")
        for r in matches:
            r.add_provenance("processor", dupemsg.format(type="PMCID"))
            r.save()
            inmem[r.id] = r

    for id in dupes.get("pmid", []):
        matches = models.Record.get_by_identifier(id, job.id, "pmid")
        for r in matches:
            if r.id in inmem:
                r = inmem[r.id]
            r.add_provenance("processor", dupemsg.format(type="PMID"))
            r.save()
            inmem[r.id] = r

    for id in dupes.get("doi", []):
        matches = models.Record.get_by_identifier(id, job.id, "doi")
        for r in matches:
            if r.id in inmem:
                r = inmem[r.id]
            r.add_provenance("processor", dupemsg.format(type="DOI"))
            r.save()

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
            else:
                err = str(len(mds)) + " metadata records found for PMCID " + msg.record.pmcid + " - unable to uniquely identify by this identifier"
                app.logger.info(err)
                msg.record.add_provenance("processor", err)
        except epmc.EuropePMCException as e:
            # log, then just try the next one
            code = "None"
            if e.response is not None:
                code = str(e.response.status_code)
            app.logger.info("EPMC API returned " + code + " to request for " + msg.record.pmcid)
            msg.record.add_provenance("processor", "Received error from EPMC on request for " + msg.record.pmcid)

    # if we find 0 or > 1 via the pmcid, try again with the pmid
    if msg.record.pmid is not None:
        app.logger.info("Requesting EPMC metadata by PMID " + msg.record.pmid)
        try:
            mds = epmc.EuropePMC.get_by_pmid(msg.record.pmid)
            if len(mds) == 1:
                app.logger.info("EPMC metadata found")
                return mds[0], 1.0
            else:
                err = str(len(mds)) + " metadata records found for PMID " + msg.record.pmid + " - unable to uniquely identify by this identifier"
                app.logger.info(err)
                msg.record.add_provenance("processor", err)
        except epmc.EuropePMCException as e:
            # log, then just try the next one
            code = "None"
            if e.response is not None:
                code = str(e.response.status_code)
            app.logger.info("EPMC API returned " + code + " to request for " + msg.record.pmid)
            msg.record.add_provenance("processor", "Received error from EPMC on request for " + msg.record.pmid)

    # if we find 0 or > 1 via the pmid, try again with the doi
    if msg.record.doi is not None:
        app.logger.info("Requesting EPMC metadata by DOI " + msg.record.doi)
        try:
            mds = epmc.EuropePMC.get_by_doi(msg.record.doi)
            if len(mds) == 1:
                app.logger.info("EPMC metadata found")
                return mds[0], 1.0
            else:
                err = str(len(mds)) + " metadata records found for DOI " + msg.record.doi + " - unable to uniquely identify by this identifier"
                app.logger.info(err)
                msg.record.add_provenance("processor", err)
        except epmc.EuropePMCException as e:
            # log, then just try the next one
            code = "None"
            if e.response is not None:
                code = str(e.response.status_code)
            app.logger.info("EPMC API returned " + code + " to request for " + msg.record.doi)
            msg.record.add_provenance("processor", "Received error from EPMC on request for " + msg.record.doi)

    if msg.record.title is not None:
        app.logger.info("Requesting EPMC metadata by exact Title " + msg.record.title)
        try:
            mds = epmc.EuropePMC.title_exact(msg.record.title)
            if len(mds) == 1:
                app.logger.info("EPMC metadata found")
                return mds[0], 0.9
            else:
                err = str(len(mds)) + " metadata records found for exact title match - unable to uniquely identify by this string"
                app.logger.info(err)
                msg.record.add_provenance("processor", err)
        except epmc.EuropePMCException as e:
            # log, then just try the next one
            code = "None"
            if e.response is not None:
                code = str(e.response.status_code)
            app.logger.info("EPMC API returned " + code + " to request for exact title")
            msg.record.add_provenance("processor", "Received error from EPMC on request for exact title")

        app.logger.info("Requesting EPMC metadata by fuzzy Title " + msg.record.title)
        try:
            mds = epmc.EuropePMC.title_approximate(msg.record.title)
            if len(mds) == 1:
                app.logger.info("EPMC metadata found")
                return mds[0], 0.7
            else:
                err = str(len(mds)) + " metadata records found for fuzzy title match - unable to uniquely identify by this method"
                app.logger.info(err)
                msg.record.add_provenance("processor", err)
        except epmc.EuropePMCException as e:
            # log, then just try the next one
            code = "None"
            if e.response is not None:
                code = str(e.response.status_code)
            app.logger.info("EPMC API returned " + code + " to request for fuzzy title")
            msg.record.add_provenance("processor", "Received error from EPMC on request for fuzzy title")

    app.logger.info("EPMC metadata not found by any means available")
    msg.record.add_provenance("processor", "EPMC metadata not found by any means available")
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
            obj = {"id" : msg.record.pmcid, "type" : "pmcid"}
            if obj not in msg.oag_register:
                msg.oag_register.append(obj)
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
        obj = {"id" : msg.record.doi, "type" : "doi"}
        if obj not in msg.oag_register:
            msg.oag_register.append(obj)
        msg.record.in_oag = True
        msg.record.oag_doi = "sent"
        msg.record.save()
        return

    # lowest priority is to send the pmid if there is one
    if msg.record.pmid is not None:
        app.logger.info("Sending PMID " + msg.record.pmid + " to OAG for record " + msg.record.id)
        obj = {"id" : msg.record.pmid, "type" : "pmid"}
        if obj not in msg.oag_register:
            msg.oag_register.append(obj)
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
    if journals is None:
        app.logger.info("Got no response from DOAJ")
        msg.record.add_provenance("doaj", "unable to retrieve data from DOAJ at this time")
        return None
    else:
        return len(journals) > 0

def hybrid_or_oa(msg):
    oajournal = doaj_lookup(msg)
    if oajournal is None:
        # doaj lookup failed
        return
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

    # in epmc?
    if epmc_md.in_epmc is not None:
        msg.record.in_epmc = epmc_md.in_epmc == "Y"

    # is oa?
    if epmc_md.is_oa is not None:
        msg.record.is_oa = epmc_md.is_oa == "Y"

    # any issns
    if epmc_md.issn is not None:
        msg.record.add_issn(epmc_md.issn)
    if epmc_md.essn is not None:
        msg.record.add_issn(epmc_md.essn)

    # the journal
    if epmc_md.journal is not None:
        msg.record.journal = epmc_md.journal

def extract_fulltext_info(msg, fulltext):
    # record that the fulltext exists in the first place
    msg.record.has_ft_xml = True
    msg.record.add_provenance("processor", "Found fulltext XML in EPMC")

    # record whether the fulltext tells us this is an author manuscript
    msg.record.aam = fulltext.is_aam
    msg.record.aam_from_xml = True
    msg.record.add_provenance("processor", "AAM status set from Fulltext XML")

def extract_fulltext_licence(msg, fulltext):
    type, url, para = fulltext.get_licence_details()

    if type is not None:
        for t, c in licences.types.iteritems():
            if type == t:
                msg.record.licence_type = c
                msg.record.add_provenance("processor", "Fulltext XML specifies licence type as %(license)s" % {"license" : type})
                msg.record.licence_source = "epmc_xml"
                return

    # if there is a url, and it begins with one of the urls we know about (so we can capture multiple cc licence versions with one url)
    if url is not None:
        urls = [u for u, l in licences.urls]
        for u in urls:
            if url.startswith(u):
                msg.record.licence_type = [l for u2, l in licences.urls if u == u2][0]
                msg.record.add_provenance("processor", "Fulltext XML specifies licence url as %(url)s which gives us licence type %(license)s" % {"url" : url, "license" : msg.record.licence_type})
                msg.record.licence_source = "epmc_xml"
                return

    # if there is some text, and we can find one of our substrings in it
    if para is not None:
        for ss, t in licences.substrings:
            if ss in para:
                msg.record.licence_type = t
                msg.record.add_provenance("processor", "Fulltext XML licence description contains the licence text %(text)s which gives us licence type %(license)s" % {"text" : ss, "license" : t})
                msg.record.licence_source = "epmc_xml"
                return

    # finally, if there is licence information, but we can't recognise it, then record a non-standard licence
    if type is not None or url is not None or para is not None:
        msg.record.licence_type = "non-standard-licence"
        msg.record.add_provenance("processor", "Fulltext XML contained licence information, but we could not recognise it as a standard open licence; recording non-standard-licence")
        msg.record.licence_source = "epmc_xml"
        return


def add_to_rerun(record, idtype, oag_rerun):
    if idtype == "pmcid":
        if record.doi is not None:
            obj = {"id" : record.doi, "type" : "doi"}
            if obj not in oag_rerun:
                oag_rerun.append(obj)
            return True
        if record.pmid is not None:
            obj = {"id" : record.pmid, "type" : "pmid"}
            if obj not in oag_rerun:
                oag_rerun.append(obj)
            return True
        return False
    elif idtype == "doi":
        if record.pmid is not None:
            obj = {"id" : record.pmid, "type" : "pmid"}
            if obj not in oag_rerun:
                oag_rerun.append(obj)
            return True
        return False
    elif idtype == "pmid":
        return False

#################################################################

def oag_callback_closure():
    def oag_callback(event, state):
        # follow the link over to the related spreadsheet
        oagrlink = models.OAGRLink.by_oagr_id(state.id)
        ssjob = models.SpreadsheetJob.pull(oagrlink.spreadsheet_id)

        # a register of identifiers which need to be re-run
        oag_rerun = []

        if event == "cycle":
            # handle the successes
            successes = state.flush_success()
            for s in successes:
                oag_record_callback(s, oag_rerun, ssjob)

            # handle the errors
            errors = state.flush_error()
            for e in errors:
                oag_record_callback(e, oag_rerun, ssjob)

            """
            else:
                # it's possible that the spreadsheet job has finished, so we need
                # to check and update if so
                time.sleep(2)   # just to give the index a bit of time to refresh
                pc = ssjob.pc_complete
                if int(pc) == 100:
                    ssjob.status_code = "complete"
                    ssjob.save()
                    send_complete_mail(ssjob)
            """

        elif event == "finished":
            app.logger.info("OAGR job event finished - " + str(len(state.maxed.keys())) + " maxed")

            # check all the identifiers that got maxed, and record errors against them
            # in their individual records
            for id, obj in state.maxed.iteritems():
                record_maxed(id, obj, ssjob, oag_rerun)

            # it's possible that the spreadsheet job has finished, so we need
            # to check and update if so
            time.sleep(2)   # just to give the index a bit of time to refresh
            pc = ssjob.pc_complete
            if int(pc) == 100:
                ssjob.status_code = "complete"
                ssjob.save()
                send_complete_mail(ssjob)

        # if there is anything to reprocess, do that
        if len(oag_rerun) > 0:
            # put anything that needs to be reprocessed back on the job queue
            process_oag(oag_rerun, ssjob)

    return oag_callback

def record_maxed(id, result, ssjob, oag_rerun):
    def process(record, type, oag_rerun):
        record.add_provenance("oag", "Attempted to retrieve {x} {y} times from OAG, and got no result; giving up.".format(x=id, y=result.get("requested")))
        added = add_to_rerun(record, type, oag_rerun)
        if not added:
            record.oag_complete = True
        record.save()

    records = models.Record.get_by_identifier(id, ssjob.id)
    found = 0
    for record in records:
        found += 1

        # set its in_oag flag and re-save it
        record.in_oag = False

        # by this point we must know the type
        type = None
        if id == record.pmcid:
            type = "pmcid"
            record.oag_pmcid = "error"
        elif id == record.pmid:
            type = "pmid"
            record.oag_pmid = "error"
        elif id == record.doi:
            type = "doi"
            record.oag_doi = "error"
        else:
            app.logger.info("unable to determine the type for " + str(id))

        if type is not None:
            process(record, type, oag_rerun)
        else:
            app.logger.info("type of id was not one of pmcid, doi, pmid")
            continue

    # summary log of what we did
    if found == 0:
        app.logger.info("was unable to relate OAG response to record")
    else:
        app.logger.info("Updated {x} records from OAG maxed identifiers".format(x=found))

def send_complete_mail(job):
    if job.contact_email is None:
        app.logger.warn("Unable to send email for job {x} as there is no contact address".format(x=job.id))

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

    try:
        mail.send_mail(to=[job.contact_email], subject="[oac] Processing complete", template_name="emails/complete_email_template.txt", url=url)
    except:
        app.logger.warn("Problem sending email")

# create the type map which maps OAG licences to the way we want to represent them internally
TYPE_MAP = {
    "free-to-read" : "non-standard-licence",
    "other-closed" : "non-standard-licence"
}

# add to the type map the known EPMC licence types, with their canonical forms, so we get uniform representation
TYPE_MAP.update(licences.types)

def translate_licence_type(ltype):
    if ltype in TYPE_MAP:
        return TYPE_MAP.get(ltype)
    return ltype

def oag_record_callback(result, oag_rerun, ssjob):

    def handle_error(record, idtype, error_message, oag_rerun):
        # first record an error status against the id type
        problem_id = ""
        if idtype == "pmcid":
            record.oag_pmcid = "error"
            problem_id = record.pmcid
        elif idtype == "pmid":
            record.oag_pmid = "error"
            problem_id = record.pmid
        elif idtype == "doi":
            record.oag_doi = "error"
            problem_id = record.doi

        record.add_provenance("oag", problem_id + " - " + error_message)

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

        record.licence_type = translate_licence_type(result.get("license", [{}])[0].get("type"))
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

        # get the id that resulted in the success
        success_id = ""
        if idtype == "pmcid":
            success_id = record.pmcid
        elif idtype == "pmid":
            success_id = record.pmid
        elif idtype == "doi":
            success_id = record.doi

        # get the OAG provenance description and put it into the record
        prov = result.get("license", [{}])[0].get("provenance", {}).get("description")
        record.add_provenance("oag", success_id + " - " + prov)

        if result.get("license", [{}])[0].get("type", "failed-to-obtain-license") == "failed-to-obtain-license":
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

    # try to get record from the id, job id, and type (note that there could be one, if the user has
    # given us duplicate ids, or we discovered two ids share a duplicate along the way
    records = models.Record.get_by_identifier(id, ssjob.id, type)
    app.logger.info("handling OAG response for " + id)

    # each record we have that matches this identifier has to be processed in the same
    # way, so we just iterate over them
    found = 0
    for record in records:
        found += 1

        assert isinstance(record, models.Record)    # For pycharm type inspection

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
                # return
                continue                # These continues are here not because they have any immediate effect
            else:
                if not record.aam_from_xml:
                    handle_aam(result, record)
                process_licence(result, record, type, oag_rerun)
                continue                # but because they remind us that this is the end of the processing chain
        elif type == "doi":
            if iserror:
                handle_error(record, "doi", result.get("error"), oag_rerun)
                # return
                continue                # for this particular record.  If we add further logic below, this will
            else:
                process_licence(result, record, type, oag_rerun)
                continue                # remind us to take that into consideration, and we won't accidentally
        elif type == "pmid":
            if iserror:
                handle_error(record, "pmid", result.get("error"), oag_rerun)
                continue                # do more work on the record than we intended
            else:
                process_licence(result, record, type, oag_rerun)
                continue
        else:
            app.logger.info("type of id was not one of pmcid, doi, pmid")
            continue

    # summary log of what we did
    if found == 0:
        app.logger.info("was unable to relate OAG response to record")
    else:
        app.logger.info("Updated {x} records from OAG response".format(x=found))





