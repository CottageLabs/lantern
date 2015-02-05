from octopus.modules.es import testindex
from octopus.modules.epmc import client as epmc
from octopus.modules.oag import oagr
from octopus.modules.oag import client as oagclient
from service import workflow, models
import time, requests, json, os
from lxml import etree

post_counter = 0

EPMC_MD = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "resources", "epmc_md.json")
EPMC_FT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "resources", "epmc_ft.xml")

class TestWorkflow(testindex.ESTestCase):
    def setUp(self):
        super(TestWorkflow, self).setUp()
        self.old_post = requests.post
        self.old_doaj_lookup = workflow.doaj_lookup
        self.old_get_epmc_md = workflow.get_epmc_md
        self.old_get_epmc_fulltext = workflow.get_epmc_fulltext
        self.old_process_oag = workflow.process_oag

    def tearDown(self):
        super(TestWorkflow, self).tearDown()
        requests.post = self.old_post
        workflow.doaj_lookup = self.old_doaj_lookup
        workflow.get_epmc_md = self.old_get_epmc_md
        workflow.get_epmc_fulltext = self.old_get_epmc_fulltext
        workflow.process_oag = self.old_process_oag

    def test_01_oag_rerun(self):
        record = models.Record()

        # PMCID sent, no DOI or PMID
        oag = []
        added = workflow.add_to_rerun(record, "pmcid", oag)
        assert len(oag) == 0
        assert added is False

        # PMCID sent, PMID only
        record.pmid = "1234"
        oag = []
        added = workflow.add_to_rerun(record, "pmcid", oag)
        assert len(oag) == 1
        assert oag[0]["id"] == "1234"
        assert oag[0]["type"] == "pmid"
        assert added is True

        # PMCID sent, DOI only
        del record.pmid
        record.doi = "10.1234"
        oag = []
        workflow.add_to_rerun(record, "pmcid", oag)
        assert len(oag) == 1
        assert oag[0]["id"] == "10.1234"
        assert oag[0]["type"] == "doi"

        # PMCID sent, PMID and DOI available
        record.pmid = "1234"
        record.doi = "10.1234"
        oag = []
        workflow.add_to_rerun(record, "pmcid", oag)
        assert len(oag) == 1
        assert oag[0]["id"] == "10.1234"
        assert oag[0]["type"] == "doi"

        # DOI sent, no PMID
        del record.pmid
        record.doi = "10.1234"
        oag = []
        workflow.add_to_rerun(record, "doi", oag)
        assert len(oag) == 0

        # DOI sent, PMID available
        record.pmid = "1234"
        record.doi = "10.1234"
        oag = []
        workflow.add_to_rerun(record, "doi", oag)
        assert len(oag) == 1
        assert oag[0]["id"] == "1234"
        assert oag[0]["type"] == "pmid"

        # PMID sent
        record.pmid = "1234"
        del record.doi
        oag = []
        workflow.add_to_rerun(record, "pmid", oag)
        assert len(oag) == 0

        # duplicate of existing object on stack
        oag = [{"id" : "1234", "type" : "pmid"}]
        workflow.add_to_rerun(record, "pmid", oag)
        assert len(oag) == 1

    def test_02_send_to_oag(self):
        record = models.Record()

        # Has PMCID, AAM and Licence
        record.pmcid = "PMC1234"
        record.aam_from_xml = True
        record.licence_type = "CC BY"
        record.id = record.makeid()
        oag = []
        msg = workflow.WorkflowMessage(record=record, oag_register=oag)
        workflow.register_with_oag(msg)
        assert len(oag) == 0

        # Has PMCID, AAM, but no licence
        record.pmcid = "PMC1234"
        record.aam_from_xml = True
        del record.licence_type
        oag = []
        msg = workflow.WorkflowMessage(record=record, oag_register=oag)
        workflow.register_with_oag(msg)
        assert len(oag) == 1
        assert oag[0].get("id") == "PMC1234"
        assert oag[0].get("type") == "pmcid"

        # Has PMCID, not AAM, Licence
        record.pmcid = "PMC1234"
        record.aam_from_xml = False
        record.licence_type = "CC BY"
        oag = []
        msg = workflow.WorkflowMessage(record=record, oag_register=oag)
        workflow.register_with_oag(msg)
        assert len(oag) == 1
        assert oag[0].get("id") == "PMC1234"
        assert oag[0].get("type") == "pmcid"

        # Has PMCID, not AAM or Licence
        record.pmcid = "PMC1234"
        record.aam_from_xml = False
        del record.licence_type
        oag = []
        msg = workflow.WorkflowMessage(record=record, oag_register=oag)
        workflow.register_with_oag(msg)
        assert len(oag) == 1
        assert oag[0].get("id") == "PMC1234"
        assert oag[0].get("type") == "pmcid"

        # No PMCID, has DOI and Licence
        del record.pmcid
        record.aam_from_xml = False
        record.licence_type = "CC BY"
        oag = []
        msg = workflow.WorkflowMessage(record=record, oag_register=oag)
        workflow.register_with_oag(msg)
        assert len(oag) == 0

        # No PMCID, has DOI, no Licence
        record.doi = "10.1234"
        del record.licence_type
        oag = []
        msg = workflow.WorkflowMessage(record=record, oag_register=oag)
        workflow.register_with_oag(msg)
        assert len(oag) == 1
        assert oag[0].get("id") == "10.1234"
        assert oag[0].get("type") == "doi"

        # No PMCID or DOI, has PMID but no Licence
        del record.doi
        record.pmid = "1234"
        oag = []
        msg = workflow.WorkflowMessage(record=record, oag_register=oag)
        workflow.register_with_oag(msg)
        assert len(oag) == 1
        assert oag[0].get("id") == "1234"
        assert oag[0].get("type") == "pmid"

        # No identifiers or licence
        del record.pmid
        del record.licence_type
        oag = []
        msg = workflow.WorkflowMessage(record=record, oag_register=oag)
        workflow.register_with_oag(msg)
        assert len(oag) == 0

        # identifier which has previously been added to the run
        record.pmid = "1234"
        oag = [{"id" : "1234", "type" : "pmid"}]
        msg = workflow.WorkflowMessage(record=record, oag_register=oag)
        workflow.register_with_oag(msg)
        assert len(oag) == 1


    def test_03_handle_oag_response_01_pmcid_success(self):
        # first make ourselves a job/record that we want to enhance
        job = models.SpreadsheetJob()
        job.save()

        record = models.Record()
        record.upload_id = job.id
        record.pmcid = "PMC1234"
        record.save()

        time.sleep(2)

        # construct the OAG response object, which has detected a licence
        oag_result = {
            "identifier" : [{
                "id" : "PMC1234",
                "type" : "pmcid"
            }],
            "license" : [{
                "type" : "cc-by",
                "provenance" : {
                    "accepted_author_manuscript" : True,   # FIXME: provisional
                    "description" : "Provenance PMC1234"
                }
            }]
        }

        # call the oag record callback
        oag_rerun = []
        workflow.oag_record_callback(oag_result, oag_rerun, job)

        # should not have added anything to the rerun
        assert len(oag_rerun) == 0

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("PMC1234", job.id, "pmcid").next()
        assert isinstance(r2, models.Record)
        assert r2.id == record.id
        assert r2.pmcid == "PMC1234"

        # licence added, source=epmc, pmcid=success, provenance added, aam set
        assert r2.licence_type == "cc-by"
        assert r2.licence_source == "epmc"
        assert r2.oag_pmcid == "success"
        assert r2.aam_from_epmc is True
        assert r2.aam is True
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 2
        assert "PMC1234 - Provenance PMC1234" in provs
        assert "Detected AAM status from EPMC web page" in provs

    def test_03_handle_oag_response_02_pmcid_fto(self):
        # first make ourselves a record that we want to enhance
        job = models.SpreadsheetJob()
        job.save()

        record = models.Record()
        record.upload_id = job.id
        record.pmcid = "PMC1234"
        record.doi = "10.1234"
        record.save()
        time.sleep(2)

        # construct the OAG response object, which has detected a licence
        oag_result = {
            "identifier" : [{
                "id" : "PMC1234",
                "type" : "pmcid"
            }],
            "license" : [{
                "type" : "failed-to-obtain-license",
                "provenance" : {
                    "accepted_author_manuscript" : True,   # FIXME: provisional
                    "description" : "FTO PMC1234"
                }
            }]
        }

        # call the oag record callback
        oag_rerun = []
        workflow.oag_record_callback(oag_result, oag_rerun, job)

        # should have added the DOI to the re-run
        assert len(oag_rerun) == 1
        assert oag_rerun[0]["id"] == "10.1234"
        assert oag_rerun[0]["type"] == "doi"

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("PMC1234", job.id, "pmcid").next()
        assert isinstance(r2, models.Record)

        # provenance added, pmcid=fto, aam set
        assert r2.licence_type is None
        assert r2.oag_pmcid == "fto"
        assert r2.aam_from_epmc is True
        assert r2.aam is True
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 2
        assert "PMC1234 - FTO PMC1234" in provs
        assert "Detected AAM status from EPMC web page" in provs

    def test_03_handle_oag_response_03_pmcid_no_aam(self):
        # first make ourselves a record that we want to enhance
        job = models.SpreadsheetJob()
        job.save()

        record = models.Record()
        record.upload_id = job.id
        record.pmcid = "PMC1234"
        record.save()
        time.sleep(2)

        # construct the OAG response object, which has detected a licence
        oag_result = {
            "identifier" : [{
                "id" : "PMC1234",
                "type" : "pmcid"
            }],
            "license" : [{
                "type" : "failed-to-obtain-license",
                "provenance" : {
                    "accepted_author_manuscript" : False,   # FIXME: provisional
                    "description" : "No Licence PMC1234"
                }
            }]
        }

        # call the oag record callback
        oag_rerun = []
        workflow.oag_record_callback(oag_result, oag_rerun, job)

        # should not have added anything to the rerun
        assert len(oag_rerun) == 0

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("PMC1234", job.id, "pmcid").next()
        assert isinstance(r2, models.Record)

        # expecting no licence or aam
        assert r2.licence_type is None
        assert r2.licence_source is None
        assert r2.oag_pmcid == "fto"
        assert r2.aam_from_epmc is True
        assert r2.aam is False
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 2
        assert "PMC1234 - No Licence PMC1234" in provs
        assert "Detected AAM status from EPMC web page" in provs

    def test_03_handle_oag_response_04_pmcid_no_change(self):
        # first make ourselves a record that we want to enhance
        job = models.SpreadsheetJob()
        job.save()

        record = models.Record()
        record.upload_id = job.id
        record.pmcid = "PMC1234"
        record.licence_type = "CC BY"
        record.aam = True
        record.aam_from_xml = True
        record.save()
        time.sleep(2)

        # construct the OAG response object, which has detected a licence
        oag_result = {
            "identifier" : [{
                "id" : "PMC1234",
                "type" : "pmcid"
            }],
            "license" : [{
                "type" : "failed-to-obtain-license",
                "provenance" : {
                    "accepted_author_manuscript" : False,   # FIXME: provisional
                    "description" : "You won't see this PMC1234"
                }
            }]
        }

        # call the oag record callback
        oag_rerun = []
        workflow.oag_record_callback(oag_result, oag_rerun, job)

        # should not have added anything to the rerun
        assert len(oag_rerun) == 0

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("PMC1234", job.id, "pmcid").next()
        assert isinstance(r2, models.Record)

        # expecting no changes
        assert r2.licence_type == "CC BY"
        assert r2.licence_source is None
        assert r2.oag_pmcid is None
        assert r2.aam_from_epmc is False
        assert r2.aam is True
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 0

    def test_03_handle_oag_response_05_pmcid_error(self):
        # first make ourselves a record that we want to enhance
        job = models.SpreadsheetJob()
        job.save()

        record = models.Record()
        record.upload_id = job.id
        record.pmcid = "PMC1234"
        record.pmid = "1234"
        record.save()
        time.sleep(2)

        # construct the OAG response object, which has detected a licence
        oag_result = {
            "identifier" : {
                "id" : "PMC1234",
                "type" : "pmcid"
            },
            "error" : "broken!"
        }

        # call the oag record callback
        oag_rerun = []
        workflow.oag_record_callback(oag_result, oag_rerun, job)

        # should have added the PMID to the re-run
        assert len(oag_rerun) == 1
        assert oag_rerun[0]["id"] == "1234"
        assert oag_rerun[0]["type"] == "pmid"

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("PMC1234", job.id, "pmcid").next()
        assert isinstance(r2, models.Record)

        # provenance added, pmcid=error, pmid reprocess
        assert r2.licence_type is None
        assert r2.oag_pmcid == "error"
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 1
        assert "PMC1234 - broken!" in provs

    def test_03_handle_oag_response_06_doi_success(self):
        # first make ourselves a record that we want to enhance
        job = models.SpreadsheetJob()
        job.save()

        record = models.Record()
        record.upload_id = job.id
        record.doi = "10.1234"
        record.save()
        time.sleep(2)

        # construct the OAG response object, which has detected a licence
        oag_result = {
            "identifier" : [{
                "id" : "10.1234",
                "type" : "doi"
            }],
            "license" : [{
                "type" : "cc-by",
                "provenance" : {
                    "description" : "Provenance 10.1234"
                }
            }]
        }

        # call the oag record callback
        oag_rerun = []
        workflow.oag_record_callback(oag_result, oag_rerun, job)

        # should not have added anything to the rerun
        assert len(oag_rerun) == 0

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("10.1234", job.id).next() # leave out the "doi" type just for the hell of it
        assert isinstance(r2, models.Record)

        # licence added, source=publisher, doi=success, provenance added
        assert r2.licence_type == "cc-by"
        assert r2.licence_source == "publisher"
        assert r2.oag_doi == "success"
        assert r2.aam is None
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 1
        assert "10.1234 - Provenance 10.1234" in provs

    def test_03_handle_oag_response_07_doi_fto(self):
        # first make ourselves a record that we want to enhance
        job = models.SpreadsheetJob()
        job.save()

        record = models.Record()
        record.upload_id = job.id
        record.doi = "10.1234"
        record.pmid = "1234"
        record.save()
        time.sleep(2)

        # construct the OAG response object, which has detected a licence
        oag_result = {
            "identifier" : [{
                "id" : "10.1234",
                "type" : "doi"
            }],
            "license" : [{
                "type" : "failed-to-obtain-license",
                "provenance" : {
                    "description" : "FTO 10.1234"
                }
            }]
        }

        # call the oag record callback
        oag_rerun = []
        workflow.oag_record_callback(oag_result, oag_rerun, job)

        # should have added the DOI to the re-run
        assert len(oag_rerun) == 1
        assert oag_rerun[0]["id"] == "1234"
        assert oag_rerun[0]["type"] == "pmid"

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("10.1234", job.id).next()
        assert isinstance(r2, models.Record)

        # provenance added, doi=fto, pmid reprocess
        assert r2.licence_type is None
        assert r2.oag_doi == "fto"
        assert r2.aam is None
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 1
        assert "10.1234 - FTO 10.1234" in provs

    def test_03_handle_oag_response_08_doi_error(self):
        # first make ourselves a record that we want to enhance
        job = models.SpreadsheetJob()
        job.save()

        record = models.Record()
        record.upload_id = job.id
        record.doi = "10.1234"
        record.save()
        time.sleep(2)

        # construct the OAG response object, which has detected a licence
        oag_result = {
            "identifier" : {
                "id" : "10.1234",
                "type" : "doi"
            },
            "error" : "broken!"
        }

        # call the oag record callback
        oag_rerun = []
        workflow.oag_record_callback(oag_result, oag_rerun, job)

        # nothing to re-run
        assert len(oag_rerun) == 0

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("10.1234", job.id).next()
        assert isinstance(r2, models.Record)

        # provenance added, pmcid=error, pmid reprocess
        assert r2.licence_type is None
        assert r2.oag_doi == "error"
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 1
        assert "10.1234 - broken!" in provs

    def test_03_handle_oag_response_09_pmid_success(self):
        # first make ourselves a record that we want to enhance
        job = models.SpreadsheetJob()
        job.save()

        record = models.Record()
        record.upload_id = job.id
        record.pmid = "1234"
        record.save()
        time.sleep(2)

        # construct the OAG response object, which has detected a licence
        oag_result = {
            "identifier" : [{
                "id" : "1234",
                "type" : "pmid"
            }],
            "license" : [{
                "type" : "cc-by",
                "provenance" : {
                    "description" : "Provenance 1234"
                }
            }]
        }

        # call the oag record callback
        oag_rerun = []
        workflow.oag_record_callback(oag_result, oag_rerun, job)

        # should not have added anything to the rerun
        assert len(oag_rerun) == 0

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("1234", job.id, "pmid").next()
        assert isinstance(r2, models.Record)

        # licence added, source=publisher, doi=success, provenance added
        assert r2.licence_type == "cc-by"
        assert r2.licence_source == "publisher"
        assert r2.oag_pmid == "success"
        assert r2.aam is None
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 1
        assert "1234 - Provenance 1234" in provs

    def test_03_handle_oag_response_10_pmid_fto(self):
        # first make ourselves a record that we want to enhance
        job = models.SpreadsheetJob()
        job.save()

        record = models.Record()
        record.upload_id = job.id
        record.pmid = "1234"
        record.save()
        time.sleep(2)

        # construct the OAG response object, which has detected a licence
        oag_result = {
            "identifier" : [{
                "id" : "1234",
                "type" : "pmid"
            }],
            "license" : [{
                "type" : "failed-to-obtain-license",
                "provenance" : {
                    "description" : "FTO 1234"
                }
            }]
        }

        # call the oag record callback
        oag_rerun = []
        workflow.oag_record_callback(oag_result, oag_rerun, job)

        # nothing left to re-run
        assert len(oag_rerun) == 0

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("1234", job.id, "pmid").next()
        assert isinstance(r2, models.Record)

        # provenance added, doi=fto, pmid reprocess
        assert r2.licence_type is None
        assert r2.oag_pmid == "fto"
        assert r2.aam is None
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 1
        assert "1234 - FTO 1234" in provs

    def test_03_handle_oag_response_11_pmid_error(self):
        # first make ourselves a record that we want to enhance
        job = models.SpreadsheetJob()
        job.save()

        record = models.Record()
        record.upload_id = job.id
        record.pmid = "1234"
        record.save()
        time.sleep(2)

        # construct the OAG response object, which has detected a licence
        oag_result = {
            "identifier" : {
                "id" : "1234",
                "type" : "pmid"
            },
            "error" : "broken!"
        }

        # call the oag record callback
        oag_rerun = []
        workflow.oag_record_callback(oag_result, oag_rerun, job)

        # nothing to re-run
        assert len(oag_rerun) == 0

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("1234", job.id, "pmid").next()
        assert isinstance(r2, models.Record)

        # provenance added, pmcid=error, pmid reprocess
        assert r2.licence_type is None
        assert r2.oag_pmid == "error"
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 1
        assert "1234 - broken!" in provs

    def test_04_process_oag(self):
        job = models.SpreadsheetJob()
        job.save()

        oag_register = [
            {"id" : "PMC1234", "type" : "pmcid"},
            {"id" : "10.1234", "type" : "doi"},
            {"id" : "10.5678", "type" : "doi"},
            {"id" : "abcd", "type" : "pmid"}
        ]

        workflow.process_oag(oag_register, job)

        time.sleep(2)

        link = models.OAGRLink.by_spreadsheet_id(job.id)
        assert link is not None
        assert link.spreadsheet_id == job.id
        assert link.oagrjob_id is not None

        oj = oagr.dao.JobsDAO.pull(link.oagrjob_id)
        assert oj is not None
        state = oj.state()
        assert len(state.pending) == 4

    def test_05_populate_identifiers(self):
        record = models.Record()
        msg = workflow.WorkflowMessage(record=record)

        data = json.loads(open(EPMC_MD, "r").read())
        epmc_md = epmc.EPMCMetadata(data)

        workflow.populate_identifiers(msg, epmc_md)

        assert record.pmcid == "PMC4219345"
        assert record.pmid == "24279897"
        assert record.doi == "10.1186/1471-2121-14-52"

        record.pmcid = "PMC000000"
        record.pmid = "0000000"
        del record.doi

        workflow.populate_identifiers(msg, epmc_md)

        assert record.pmcid == "PMC000000"
        assert record.pmid == "0000000"
        assert record.doi == "10.1186/1471-2121-14-52"

    def test_06_epmc_compliance_data(self):
        record = models.Record()
        msg = workflow.WorkflowMessage(record=record)

        data = json.loads(open(EPMC_MD, "r").read())
        epmc_md = epmc.EPMCMetadata(data)

        workflow.extract_metadata(msg, epmc_md)

        assert record.in_epmc is True
        assert record.is_oa is False
        assert len(record.issn) == 1
        assert "1471-2121" in record.issn

    def test_07_ft_info(self):
        record = models.Record()
        msg = workflow.WorkflowMessage(record=record)

        data = open(EPMC_FT, "r").read()
        ft = epmc.EPMCFullText(data)

        workflow.extract_fulltext_info(msg, ft)

        assert record.has_ft_xml is True
        assert len(record.provenance) == 2
        assert record.aam is True
        assert record.aam_from_xml is True

    def test_08_ft_licence(self):
        data = open(EPMC_FT, "r").read()
        xml = etree.fromstring(data)

        l = xml.xpath("//license")
        lp = l[0].find("license-p")

        # licence in type attribute
        l[0].set("license-type", "cc by")   # note the missing "-"; to test the licence representation variations at the same time
        l[0].set("{http://www.w3.org/1999/xlink}href", "http://random.url")
        lp.clear()
        s = etree.tostring(xml)
        ft = epmc.EPMCFullText(s)
        record = models.Record()
        msg = workflow.WorkflowMessage(record=record)
        workflow.extract_fulltext_licence(msg, ft)
        assert record.licence_type == "cc-by"
        assert record.licence_source == "epmc_xml"
        assert len(record.provenance) == 1

        # licence in href attribute
        l[0].set("license-type", "open access")
        l[0].set("{http://www.w3.org/1999/xlink}href", "http://creativecommons.org/licenses/by-nd/3.0")
        s = etree.tostring(xml)
        ft = epmc.EPMCFullText(s)
        record = models.Record()
        msg = workflow.WorkflowMessage(record=record)
        workflow.extract_fulltext_licence(msg, ft)
        assert record.licence_type == "cc-by-nd"
        assert record.licence_source == "epmc_xml"
        assert len(record.provenance) == 1

        # licence in text
        l[0].set("license-type", "open access")
        l[0].set("{http://www.w3.org/1999/xlink}href", "http://random.url")
        lp.text = "licence is <a href='http://creativecommons.org/licenses/by-nc-nd/3.0'>http://creativecommons.org/licenses/by-nc-nd/3.0</a>"
        s = etree.tostring(xml)
        ft = epmc.EPMCFullText(s)
        record = models.Record()
        msg = workflow.WorkflowMessage(record=record)
        workflow.extract_fulltext_licence(msg, ft)
        assert record.licence_type == "cc-by-nc-nd"
        assert record.licence_source == "epmc_xml"
        assert len(record.provenance) == 1

        # licence in /second/ licence paragraph
        lp.text = "some waffle"
        lp2 = etree.SubElement(l[0], "license-p")
        lp2.text = "licence is <a href='http://creativecommons.org/licenses/by/3.0'>http://creativecommons.org/licenses/by/3.0</a>"
        s = etree.tostring(xml)
        ft = epmc.EPMCFullText(s)
        record = models.Record()
        msg = workflow.WorkflowMessage(record=record)
        workflow.extract_fulltext_licence(msg, ft)
        assert record.licence_type == "cc-by"
        assert record.licence_source == "epmc_xml"
        assert len(record.provenance) == 1

        # licence in words in text
        l[0].set("license-type", "open access")
        l[0].set("{http://www.w3.org/1999/xlink}href", "http://random.url")
        lp.text = "This is a Creative Commons Attribution-NonCommercial licenced article"
        l[0].remove(lp2)
        s = etree.tostring(xml)
        ft = epmc.EPMCFullText(s)
        record = models.Record()
        msg = workflow.WorkflowMessage(record=record)
        workflow.extract_fulltext_licence(msg, ft)
        assert record.licence_type == "cc-by-nc"
        assert record.licence_source == "epmc_xml"
        assert len(record.provenance) == 1

        # licence present but unrecognised
        lp.text = "wibble wibble wobble"
        s = etree.tostring(xml)
        ft = epmc.EPMCFullText(s)
        record = models.Record()
        msg = workflow.WorkflowMessage(record=record)
        workflow.extract_fulltext_licence(msg, ft)
        assert record.licence_type == "non-standard-licence"
        assert record.licence_source == "epmc_xml"
        assert len(record.provenance) == 1

        # no licence element present
        p = l[0].getparent()
        p.remove(l[0])
        s = etree.tostring(xml)
        ft = epmc.EPMCFullText(s)
        record = models.Record()
        msg = workflow.WorkflowMessage(record=record)
        workflow.extract_fulltext_licence(msg, ft)
        assert record.licence_type is None
        assert record.licence_source is None
        assert len(record.provenance) == 0

    def test_09_hybrid_oa(self):
        def is_hybrid_lookup(msg):
            return False
        def is_oa_lookup(msg):
            return True

        # Check that an OA record is correctly identified
        workflow.doaj_lookup = is_oa_lookup
        record = models.Record()
        msg = workflow.WorkflowMessage(record=record)
        workflow.hybrid_or_oa(msg)
        assert record.journal_type == "oa"
        assert len(record.provenance) == 1

        # check that a hybrid journal is correctly identified
        workflow.doaj_lookup = is_hybrid_lookup
        record = models.Record()
        msg = workflow.WorkflowMessage(record=record)
        workflow.hybrid_or_oa(msg)
        assert record.journal_type == "hybrid"
        assert len(record.provenance) == 1

    def test_10_process_record_01_everything(self):
        def mock_get_md(*args, **kwargs):
            md = epmc.EPMCMetadata(json.loads(open(EPMC_MD, "r").read()))
            return md, 1.0

        def mock_get_ft(*args, **kwargs):
            data = open(EPMC_FT, "r").read()
            return epmc.EPMCFullText(data)

        def mock_doaj(*args, **kwargs):
            return False

        workflow.get_epmc_md = mock_get_md
        workflow.get_epmc_fulltext = mock_get_ft
        workflow.doaj_lookup = mock_doaj

        record = models.Record()
        record.pmcid = "PMC4219345"
        record.id = record.makeid()
        oag = []
        msg = workflow.WorkflowMessage(record=record, oag_register=oag)
        workflow.process_record(msg)

        assert record.confidence == 1.0
        assert record.pmcid == "PMC4219345"
        assert record.pmid == "24279897"
        assert record.doi == "10.1186/1471-2121-14-52"
        assert record.in_epmc is True
        assert record.is_oa is False
        assert len(record.issn) == 1
        assert "1471-2121" in record.issn
        assert record.id is not None # implies it has been saved
        assert record.has_ft_xml is True
        assert record.aam is True
        assert record.aam_from_xml is True
        assert record.licence_type == "cc-by"
        assert record.licence_source == "epmc_xml"
        assert record.journal_type == "hybrid"
        assert len(oag) == 0

    def test_10_process_record_02_no_md(self):
        def mock_get_md(*args, **kwargs):
            return None, None

        workflow.get_epmc_md = mock_get_md

        record = models.Record()
        record.pmcid = "PMC4219345"
        record.id = record.makeid()
        oag = []
        msg = workflow.WorkflowMessage(record=record, oag_register=oag)
        workflow.process_record(msg)

        assert record.confidence is None
        assert len(record.provenance) == 1
        assert len(oag) == 0

    def test_10_process_record_03_aam_no_licence(self):
        def mock_get_md(*args, **kwargs):
            md = epmc.EPMCMetadata(json.loads(open(EPMC_MD, "r").read()))
            return md, 1.0

        def mock_get_ft(*args, **kwargs):
            data = open(EPMC_FT, "r").read()
            xml = etree.fromstring(data)
            l = xml.xpath("//license")
            l[0].getparent().remove(l[0])
            s = etree.tostring(xml)
            return epmc.EPMCFullText(s)

        def mock_doaj(*args, **kwargs):
            return True

        workflow.get_epmc_md = mock_get_md
        workflow.get_epmc_fulltext = mock_get_ft
        workflow.doaj_lookup = mock_doaj

        record = models.Record()
        record.pmcid = "PMC4219345"
        record.id = record.makeid()
        oag = []
        msg = workflow.WorkflowMessage(record=record, oag_register=oag)
        workflow.process_record(msg)

        assert record.confidence == 1.0
        assert record.pmcid == "PMC4219345"
        assert record.pmid == "24279897"
        assert record.doi == "10.1186/1471-2121-14-52"
        assert record.in_epmc is True
        assert record.is_oa is False
        assert len(record.issn) == 1
        assert "1471-2121" in record.issn
        assert record.id is not None # implies it has been saved
        assert record.has_ft_xml is True
        assert record.aam is True
        assert record.aam_from_xml is True
        assert record.licence_type is None
        assert record.licence_source is None
        assert record.journal_type == "oa"
        assert len(oag) == 1
        assert oag[0]["id"] == "PMC4219345"
        assert oag[0]["type"] == "pmcid"

    def test_10_process_record_04_licence_no_aam(self):
        def mock_get_md(*args, **kwargs):
            md = epmc.EPMCMetadata(json.loads(open(EPMC_MD, "r").read()))
            return md, 1.0

        def mock_get_ft(*args, **kwargs):
            data = open(EPMC_FT, "r").read()
            xml = etree.fromstring(data)
            aids = xml.xpath("//article-id[@pub-id-type='manuscript']")
            aids[0].getparent().remove(aids[0])
            s = etree.tostring(xml)
            return epmc.EPMCFullText(s)

        def mock_doaj(*args, **kwargs):
            return True

        workflow.get_epmc_md = mock_get_md
        workflow.get_epmc_fulltext = mock_get_ft
        workflow.doaj_lookup = mock_doaj

        record = models.Record()
        record.pmcid = "PMC4219345"
        record.id = record.makeid()
        oag = []
        msg = workflow.WorkflowMessage(record=record, oag_register=oag)
        workflow.process_record(msg)

        assert record.confidence == 1.0
        assert record.pmcid == "PMC4219345"
        assert record.pmid == "24279897"
        assert record.doi == "10.1186/1471-2121-14-52"
        assert record.in_epmc is True
        assert record.is_oa is False
        assert len(record.issn) == 1
        assert "1471-2121" in record.issn
        assert record.id is not None # implies it has been saved
        assert record.has_ft_xml is True
        assert record.aam is False
        assert record.aam_from_xml is True
        assert record.licence_type == "cc-by"
        assert record.licence_source == "epmc_xml"
        assert record.journal_type == "oa"
        assert len(oag) == 0

    def test_10_process_record_05_no_ft(self):
        def mock_get_md(*args, **kwargs):
            md = epmc.EPMCMetadata(json.loads(open(EPMC_MD, "r").read()))
            return md, 1.0

        def mock_get_ft(*args, **kwargs):
            return None

        def mock_doaj(*args, **kwargs):
            return False

        workflow.get_epmc_md = mock_get_md
        workflow.get_epmc_fulltext = mock_get_ft
        workflow.doaj_lookup = mock_doaj

        record = models.Record()
        record.pmcid = "PMC4219345"
        record.id = record.makeid()
        oag = []
        msg = workflow.WorkflowMessage(record=record, oag_register=oag)
        workflow.process_record(msg)

        assert record.confidence == 1.0
        assert record.pmcid == "PMC4219345"
        assert record.pmid == "24279897"
        assert record.doi == "10.1186/1471-2121-14-52"
        assert record.in_epmc is True
        assert record.is_oa is False
        assert len(record.issn) == 1
        assert "1471-2121" in record.issn
        assert record.id is not None # implies it has been saved
        assert record.has_ft_xml is False
        assert record.aam is None
        assert record.aam_from_xml is False
        assert record.licence_type is None
        assert record.licence_source is None
        assert record.journal_type == "hybrid"
        assert len(oag) == 1
        assert oag[0]["id"] == "PMC4219345"
        assert oag[0]["type"] == "pmcid"

    def test_11_oag_callback_01_cycle(self):
        cb = workflow.oag_callback_closure()
        assert cb is not None

        import types
        assert type(cb) == types.FunctionType

        job = models.SpreadsheetJob()
        job.save()

        state = oagclient.RequestState(["PMC1234", "PMC9876"])
        oag_response = {
            "results" : [
                {
                    "identifier" : [{"id" : "PMC1234", "type" : "epmc", "canonical" : "PMC1234"}],
                    "license" : [
                        {
                            "type" : "cc-by",
                            "provenance" : {"description" : "SUCCESS"}
                        }
                    ]
                }
            ],
            "errors" : [
                {
                    "identifier" : {"id" : "PMC9876", "type" : "epmc", "canonical" : "PMC9876"},
                    "error" : "ERROR"
                }
            ]
        }
        state.record_result(oag_response)

        oagrlink = models.OAGRLink()
        oagrlink.spreadsheet_id = job.id
        oagrlink.oagrjob_id = state.id
        oagrlink.save()

        record = models.Record()
        record.upload_id = job.id
        record.pmcid = "PMC1234"
        record.save()

        record = models.Record()
        record.upload_id = job.id
        record.pmcid = "PMC9876"
        record.save()

        time.sleep(2)

        cb("cycle", state)

        time.sleep(2)

        r1 = models.Record.get_by_identifier("PMC1234", job.id, "pmcid").next()
        r2 = models.Record.get_by_identifier("PMC9876", job.id, "pmcid").next()

        assert r1.in_oag is False
        assert len(r1.provenance) == 1
        assert "SUCCESS" in r1.provenance[0][2]
        assert r1.oag_pmcid == "success"
        assert r1.licence_source == "epmc"
        assert r1.licence_type == "cc-by"
        assert r1.oag_complete is True

        assert r2.in_oag is False
        assert r2.oag_pmcid == "error"
        assert len(r2.provenance) == 1
        assert "ERROR" in r2.provenance[0][2]
        assert r2.oag_complete is True

    def test_11_oag_callback_02_finished(self):
        cb = workflow.oag_callback_closure()

        job = models.SpreadsheetJob()
        job.save()

        state = oagclient.RequestState(["PMC1234", "PMC9876"], max_retries=1)
        state.record_requested(["PMC1234", "PMC9876"])

        oagrlink = models.OAGRLink()
        oagrlink.spreadsheet_id = job.id
        oagrlink.oagrjob_id = state.id
        oagrlink.save()

        record = models.Record()
        record.upload_id = job.id
        record.pmcid = "PMC1234"
        record.save()

        record = models.Record()
        record.upload_id = job.id
        record.pmcid = "PMC9876"
        record.save()

        time.sleep(2)

        cb("finished", state)

        time.sleep(2)

        r1 = models.Record.get_by_identifier("PMC1234", job.id, "pmcid").next()
        r2 = models.Record.get_by_identifier("PMC9876", job.id, "pmcid").next()

        assert r1.in_oag is False
        assert len(r1.provenance) == 1
        assert r1.provenance[0][2].startswith("Attempted to retrieve PMC1234 1")
        assert r1.oag_pmcid == "error"
        assert r1.oag_complete is True

        assert r2.in_oag is False
        assert r2.oag_pmcid == "error"
        assert len(r2.provenance) == 1
        assert r2.provenance[0][2].startswith("Attempted to retrieve PMC9876 1")
        assert r2.oag_complete is True


    def test_12_licence_translate(self):
        assert workflow.translate_licence_type("free-to-read") == "non-standard-licence"

        # first make ourselves a record that we want to enhance
        job = models.SpreadsheetJob()
        job.save()

        record = models.Record()
        record.upload_id = job.id
        record.pmcid = "PMC1234"
        record.save()
        time.sleep(2)

        # construct the OAG response object, which has detected a licence
        oag_result = {
            "identifier" : [{
                "id" : "PMC1234",
                "type" : "pmcid"
            }],
            "license" : [{
                "type" : "free-to-read",
                "provenance" : {
                    "accepted_author_manuscript" : False,   # FIXME: provisional
                    "description" : "FtR PMC1234"
                }
            }]
        }

        oag_rerun = []
        workflow.oag_record_callback(oag_result, oag_rerun, job)

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("PMC1234", job.id).next()
        assert isinstance(r2, models.Record)

        assert r2.licence_type == "non-standard-licence"

    def test_13_duplicate_check(self):
        # first make ourselves a job to work on
        job = models.SpreadsheetJob()
        job.save()

        # now make a bunch of records, some unique and some duplicate

        # unique pmcid
        r = models.Record()
        r.upload_id = job.id
        r.pmcid = "PMCunique"
        r.save()

        # duplicate pmcid
        r = models.Record()
        r.upload_id = job.id
        r.pmcid = "PMCdupe"
        r.save()

        r = models.Record()
        r.upload_id = job.id
        r.pmcid = "PMCdupe"
        r.save()

        # unique pmid
        r = models.Record()
        r.upload_id = job.id
        r.pmid = "unique"
        r.save()

        # duplicate pmid
        r = models.Record()
        r.upload_id = job.id
        r.pmid = "dupe"
        r.save()

        r = models.Record()
        r.upload_id = job.id
        r.pmid = "dupe"
        r.save()

        # unique doi
        r = models.Record()
        r.upload_id = job.id
        r.doi = "10.unique"
        r.save()

        # duplicate pmcid
        r = models.Record()
        r.upload_id = job.id
        r.doi = "10.dupe"
        r.save()

        r = models.Record()
        r.upload_id = job.id
        r.doi = "10.dupe"
        r.save()

        # one that is a duplicate of everything
        r = models.Record()
        r.upload_id = job.id
        r.pmcid = "PMCdupe"
        r.pmid = "dupe"
        r.doi = "10.dupe"
        r.save()

        # one that is confused about its duplication
        r = models.Record()
        r.upload_id = job.id
        r.pmcid = "PMCdupe"
        r.pmid = "dupe"
        r.doi = "10.notdupe"
        r.save()

        time.sleep(2)

        workflow.duplicate_check(job)

        time.sleep(2)

        # for each record, check that it got the provenance

        # unique pmcid - no provenance, one result
        unique = models.Record.get_by_identifier("PMCunique", job.id, "pmcid")
        ulen = 0
        for u in unique:
            ulen += 1
            assert len(u.provenance) == 0
        assert ulen == 1

        # unique pmid - no provenance, one result
        unique = models.Record.get_by_identifier("unique", job.id, "pmid")
        ulen = 0
        for u in unique:
            ulen += 1
            assert len(u.provenance) == 0
        assert ulen == 1

        # unique doi - no provenance, one result
        unique = models.Record.get_by_identifier("10.unique", job.id, "doi")
        ulen = 0
        for u in unique:
            ulen += 1
            assert len(u.provenance) == 0
        assert ulen == 1

        # duplicates of pmcdupe
        duped = models.Record.get_by_identifier("PMCdupe", job.id, "pmcid")
        dlen = 0
        for u in duped:
            dlen += 1
            prov = False
            for p in u.provenance:
                if "PMCID" in p[2]:
                    prov = True
                    break
            assert prov
        assert dlen == 4

        # duplicates of pmid dupe
        duped = models.Record.get_by_identifier("dupe", job.id, "pmid")
        dlen = 0
        for u in duped:
            dlen += 1
            prov = False
            for p in u.provenance:
                if "PMID" in p[2]:
                    prov = True
                    break
            assert prov
        assert dlen == 4

        # duplicates of 10.dupe
        duped = models.Record.get_by_identifier("10.dupe", job.id, "doi")
        dlen = 0
        for u in duped:
            dlen += 1
            prov = False
            for p in u.provenance:
                if "DOI" in p[2]:
                    prov = True
                    break
            assert prov
        assert dlen == 3

    def test_14_oag_record_callback_duplicate(self):
        # first make ourselves a job/record that we want to enhance
        job = models.SpreadsheetJob()
        job.save()

        # make two distinct records with the same ids
        record = models.Record()
        record.upload_id = job.id
        record.pmcid = "PMC1234"
        record.save()

        record = models.Record()
        record.upload_id = job.id
        record.pmcid = "PMC1234"
        record.save()

        time.sleep(2)

        # construct the OAG response object, which has detected a licence
        oag_result = {
            "identifier" : [{
                "id" : "PMC1234",
                "type" : "pmcid"
            }],
            "license" : [{
                "type" : "cc-by",
                "provenance" : {
                    "accepted_author_manuscript" : True,
                    "description" : "Provenance PMC1234"
                }
            }]
        }

        # call the oag record callback
        oag_rerun = []
        workflow.oag_record_callback(oag_result, oag_rerun, job)

        # give the index a moment to catch up
        time.sleep(2)

        # read the duplicate records out of the index
        records = [r for r in models.Record.get_by_identifier("PMC1234", job.id, "pmcid")]

        # there should be 2 of them
        assert len(records) == 2
        for record in records:
            assert isinstance(r, models.Record)

            # both records should have the same data
            # licence added, source=epmc, pmcid=success, provenance added, aam set
            assert record.licence_type == "cc-by"
            assert record.licence_source == "epmc"
            assert record.oag_pmcid == "success"
            assert record.aam_from_epmc is True
            assert record.aam is True
            provs = [n for b, w, n in record.provenance]
            assert len(provs) == 2
            assert "PMC1234 - Provenance PMC1234" in provs
            assert "Detected AAM status from EPMC web page" in provs
            assert record.oag_complete is True

    def test_15_record_maxed_01_basic_win(self):
        job = models.SpreadsheetJob()
        job.save()

        record = models.Record()
        record.pmcid = "PMC1234"
        record.upload_id = job.id
        record.save()

        time.sleep(2)

        oag_maxed = {
            "requested": 20,
            "init" : "2001-01-01T09:30:00Z"
        }

        oag_rerun = []
        workflow.record_maxed(record.pmcid, oag_maxed, job, oag_rerun)

        time.sleep(2)

        record = models.Record.pull(record.id)
        assert record.oag_complete is True
        assert len(record.provenance) == 1

    def test_15_record_maxed_02_no_match(self):
        job = models.SpreadsheetJob()
        job.save()

        record = models.Record()
        record.pmcid = "PMC1234"
        record.upload_id = job.id
        record.save()

        time.sleep(2)

        oag_maxed = {
            "requested": 20,
            "init" : "2001-01-01T09:30:00Z"
        }

        oag_rerun = []
        workflow.record_maxed("PMC9876", oag_maxed, job, oag_rerun)

        time.sleep(2)

        record = models.Record.pull(record.id)
        assert record.oag_complete is False
        assert len(record.provenance) == 0
