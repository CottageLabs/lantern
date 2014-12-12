from octopus.modules.es import testindex
from service import workflow, models
import time, requests, json

post_counter = 0

class TestImport(testindex.ESTestCase):
    def setUp(self):
        super(TestImport, self).setUp()
        self.old_post = requests.post

    def tearDown(self):
        super(TestImport, self).tearDown()
        requests.post = self.old_post

    def test_01_oag_rerun(self):
        record = models.Record()

        # PMCID sent, no DOI or PMID
        oag = []
        workflow.add_to_rerun(record, "pmcid", oag)
        assert len(oag) == 0

        # PMCID sent, PMID only
        record.pmid = "1234"
        oag = []
        workflow.add_to_rerun(record, "pmcid", oag)
        assert len(oag) == 1
        assert oag[0]["id"] == "1234"
        assert oag[0]["type"] == "pmid"

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

    def test_02_send_to_oag(self):
        record = models.Record()

        # Has PMCID, AAM and Licence
        record.pmcid = "PMC1234"
        record.aam_from_xml = True
        record.licence_type = "CC BY"
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

    def test_03_handle_oag_response_01_pmcid_success(self):
        # first make ourselves a record that we want to enhance
        record = models.Record()
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
        workflow.oag_record_callback(oag_result, oag_rerun)

        # should not have added anything to the rerun
        assert len(oag_rerun) == 0

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("pmcid", "PMC1234")
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
        assert "Provenance PMC1234" in provs
        assert "Detected AAM status from EPMC web page" in provs

    def test_03_handle_oag_response_02_pmcid_fto(self):
        # first make ourselves a record that we want to enhance
        record = models.Record()
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
        workflow.oag_record_callback(oag_result, oag_rerun)

        # should have added the DOI to the re-run
        assert len(oag_rerun) == 1
        assert oag_rerun[0]["id"] == "10.1234"
        assert oag_rerun[0]["type"] == "doi"

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("pmcid", "PMC1234")
        assert isinstance(r2, models.Record)

        # provenance added, pmcid=fto, aam set
        assert r2.licence_type is None
        assert r2.oag_pmcid == "fto"
        assert r2.aam_from_epmc is True
        assert r2.aam is True
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 2
        assert "FTO PMC1234" in provs
        assert "Detected AAM status from EPMC web page" in provs

    def test_03_handle_oag_response_03_pmcid_no_aam(self):
        # first make ourselves a record that we want to enhance
        record = models.Record()
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
        workflow.oag_record_callback(oag_result, oag_rerun)

        # should not have added anything to the rerun
        assert len(oag_rerun) == 0

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("pmcid", "PMC1234")
        assert isinstance(r2, models.Record)

        # expecting no licence or aam
        assert r2.licence_type is None
        assert r2.licence_source is None
        assert r2.oag_pmcid == "fto"
        assert r2.aam_from_epmc is True
        assert r2.aam is False
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 2
        assert "No Licence PMC1234" in provs
        assert "Detected AAM status from EPMC web page" in provs

    def test_03_handle_oag_response_04_pmcid_no_change(self):
        # first make ourselves a record that we want to enhance
        record = models.Record()
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
        workflow.oag_record_callback(oag_result, oag_rerun)

        # should not have added anything to the rerun
        assert len(oag_rerun) == 0

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("pmcid", "PMC1234")
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
        record = models.Record()
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
        workflow.oag_record_callback(oag_result, oag_rerun)

        # should have added the PMID to the re-run
        assert len(oag_rerun) == 1
        assert oag_rerun[0]["id"] == "1234"
        assert oag_rerun[0]["type"] == "pmid"

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("pmcid", "PMC1234")
        assert isinstance(r2, models.Record)

        # provenance added, pmcid=error, pmid reprocess
        assert r2.licence_type is None
        assert r2.oag_pmcid == "error"
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 1
        assert "broken!" in provs

    def test_03_handle_oag_response_06_doi_success(self):
        # first make ourselves a record that we want to enhance
        record = models.Record()
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
        workflow.oag_record_callback(oag_result, oag_rerun)

        # should not have added anything to the rerun
        assert len(oag_rerun) == 0

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("doi", "10.1234")
        assert isinstance(r2, models.Record)

        # licence added, source=publisher, doi=success, provenance added
        assert r2.licence_type == "cc-by"
        assert r2.licence_source == "publisher"
        assert r2.oag_doi == "success"
        assert r2.aam is None
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 1
        assert "Provenance 10.1234" in provs

    def test_03_handle_oag_response_07_doi_fto(self):
        # first make ourselves a record that we want to enhance
        record = models.Record()
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
        workflow.oag_record_callback(oag_result, oag_rerun)

        # should have added the DOI to the re-run
        assert len(oag_rerun) == 1
        assert oag_rerun[0]["id"] == "1234"
        assert oag_rerun[0]["type"] == "pmid"

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("doi", "10.1234")
        assert isinstance(r2, models.Record)

        # provenance added, doi=fto, pmid reprocess
        assert r2.licence_type is None
        assert r2.oag_doi == "fto"
        assert r2.aam is None
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 1
        assert "FTO 10.1234" in provs

    def test_03_handle_oag_response_08_doi_error(self):
        # first make ourselves a record that we want to enhance
        record = models.Record()
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
        workflow.oag_record_callback(oag_result, oag_rerun)

        # nothing to re-run
        assert len(oag_rerun) == 0

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("doi", "10.1234")
        assert isinstance(r2, models.Record)

        # provenance added, pmcid=error, pmid reprocess
        assert r2.licence_type is None
        assert r2.oag_doi == "error"
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 1
        assert "broken!" in provs

    def test_03_handle_oag_response_09_pmid_success(self):
        # first make ourselves a record that we want to enhance
        record = models.Record()
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
        workflow.oag_record_callback(oag_result, oag_rerun)

        # should not have added anything to the rerun
        assert len(oag_rerun) == 0

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("pmid", "1234")
        assert isinstance(r2, models.Record)

        # licence added, source=publisher, doi=success, provenance added
        assert r2.licence_type == "cc-by"
        assert r2.licence_source == "publisher"
        assert r2.oag_pmid == "success"
        assert r2.aam is None
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 1
        assert "Provenance 1234" in provs

    def test_03_handle_oag_response_10_pmid_fto(self):
        # first make ourselves a record that we want to enhance
        record = models.Record()
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
        workflow.oag_record_callback(oag_result, oag_rerun)

        # nothing left to re-run
        assert len(oag_rerun) == 0

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("pmid", "1234")
        assert isinstance(r2, models.Record)

        # provenance added, doi=fto, pmid reprocess
        assert r2.licence_type is None
        assert r2.oag_pmid == "fto"
        assert r2.aam is None
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 1
        assert "FTO 1234" in provs

    def test_03_handle_oag_response_11_pmid_error(self):
        # first make ourselves a record that we want to enhance
        record = models.Record()
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
        workflow.oag_record_callback(oag_result, oag_rerun)

        # nothing to re-run
        assert len(oag_rerun) == 0

        # give the index a moment to catch up
        time.sleep(2)

        r2 = models.Record.get_by_identifier("pmid", "1234")
        assert isinstance(r2, models.Record)

        # provenance added, pmcid=error, pmid reprocess
        assert r2.licence_type is None
        assert r2.oag_pmid == "error"
        provs = [n for b, w, n in r2.provenance]
        assert len(provs) == 1
        assert "broken!" in provs

    def test_04_process_oag_prototype(self):
        def mock_post(*args, **kwargs):
            # fall back to original requests module
            if args[0] != "http://howopenisit.org/lookup":
                return self.old_post(*args, **kwargs)

            global post_counter

            class MockResponse(object):
                def __init__(self):
                    self.status_code = None
                    self.text = None

            if post_counter == 0:
                obj = {
                    "requested": 4,
                    "results": [
                        {
                            "identifier" : [{"id" : "PMC1234", "type" : "pmcid"}],
                            "license" : [{
                                "type" : "cc-by",
                                "provenance" : {"description" : "Provenance PMC1234"}
                            }]
                        },
                        {
                            "identifier" : [{"id" : "10.1234", "type" : "doi"}],
                            "license" : [{
                                "type" : "failed-to-obtain-license",
                                "provenance" : {"description" : "FTO 10.1234"}
                            }]
                        }
                    ],
                    "errors":[
                        {
                            "identifier" : {"id" : "10.5678", "type" : "doi"},
                            "error" : "error 1"
                        },
                        {
                            "identifier" : {"id" : "abcd", "type" : "pmid"},
                            "error" : "error 2"
                        }
                    ]
                }
            elif post_counter == 1:
                obj = {
                    "requested": 2,
                    "results": [
                        {
                            "identifier" : [{"id" : "1234", "type" : "pmid"}],
                            "license" : [{
                                "type" : "cc nc-nd",
                                "provenance" : {"description" : "WAS 10.1234"}
                            }]
                        },
                        {
                            "identifier" : [{"id" : "5678", "type" : "pmid"}],
                            "license" : [{
                                "type" : "failed-to-obtain-license",
                                "provenance" : {"description" : "FTO 5678"}
                            }]
                        }
                    ]
                }
            else:
                obj = {}
            resp = MockResponse()
            resp.status_code = 200
            resp.text = json.dumps(obj)

            post_counter += 1
            return resp

        requests.post = mock_post

        job = models.SpreadsheetJob()
        job.status_code = "processing"

        r1 = models.Record()
        r1.pmcid = "PMC1234"
        r1.save()

        r2 = models.Record()
        r2.doi = "10.1234"
        r2.pmid = "1234"
        r2.save()

        r3 = models.Record()
        r3.doi = "10.5678"
        r3.pmid = "5678"
        r3.save()

        r4 = models.Record()
        r4.pmid = "abcd"
        r4.save()

        oag_register = [
            {"id" : "PMC1234", "type" : "pmcid"},
            {"id" : "10.1234", "type" : "doi"},
            {"id" : "10.5678", "type" : "doi"},
            {"id" : "abcd", "type" : "pmid"}
        ]

        time.sleep(2)
        workflow.process_oag(oag_register, job)

        assert job.status_code == "complete"

        time.sleep(2)
        r1 = models.Record.get_by_identifier("pmcid", "PMC1234")
        r2 = models.Record.get_by_identifier("doi", "10.1234")
        r3 = models.Record.get_by_identifier("doi", "10.5678")
        r4 = models.Record.get_by_identifier("pmid", "abcd")

        assert isinstance(r1, models.Record)
        assert r1.licence_type == "cc-by"
        assert r1.oag_pmcid == "success"

        assert isinstance(r2, models.Record)
        assert r2.licence_type == "cc nc-nd"
        assert r2.oag_doi == "fto"
        assert r2.oag_pmid == "success"

        assert isinstance(r3, models.Record)
        assert r3.licence_type is None
        assert r3.oag_doi == "error"
        assert r3.oag_pmid == "fto"

        assert isinstance(r4, models.Record)
        assert r4.licence_type is None
        assert r4.oag_pmid == "error"

        assert post_counter == 2




