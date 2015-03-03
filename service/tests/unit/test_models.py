from octopus.modules.es.testindex import ESTestCase
from service.models import Record, SpreadsheetJob, OAGRLink
import time

class TestModels(ESTestCase):
    def setUp(self):
        super(TestModels, self).setUp()

    def tearDown(self):
        super(TestModels, self).tearDown()

    def test_01_spreadsheet(self):
        s = SpreadsheetJob()
        s.filename = "myfile.csv"
        s.contact_email = "contact@email.com"
        s.status_code = "processing"
        s.status_message = "currently working on it!"

        assert s.filename == "myfile.csv"
        assert s.contact_email == "contact@email.com"
        assert s.status_code == "processing"
        assert s.status_message == "currently working on it!"


    def test_02_record(self):
        r = Record()
        r.upload_id = "1234"
        r.upload_pos = "234"
        r.set_source_data(
                          pmcid="PMC12345678",
                          pmid="98765432",
                          doi="10.whatever",
                          article_title="A study of sorts",
                          )

        r.pmcid = "PMC12345678"
        r.pmid = "98765432"
        r.doi = "10.whatever"
        r.title = "A study of sorts"
        r.has_ft_xml = True
        r.aam_from_xml = False
        r.aam_from_epmc = True
        r.issn = "1234-5678"
        r.in_oag = True
        r.oag_pmcid = "not_sent"
        r.oag_doi = "sent"
        r.oag_pmid = "fto"
        r.in_epmc = True
        r.is_oa = False
        r.aam = True
        r.licence_type = "CC BY"
        r.licence_source = "epmc"
        r.journal_type = "hybrid"
        r.confidence = "0.8"
        r.add_provenance("richard", "provenance 1")
        r.add_provenance("wellcome", "provenance 2")

        assert r.upload_id == "1234"
        assert r.upload_pos == 234
        assert r.pmcid == "PMC12345678"
        assert r.pmid == "98765432"
        assert r.doi == "10.whatever"
        assert r.title == "A study of sorts"
        assert r.has_ft_xml
        assert not r.aam_from_xml
        assert r.aam_from_epmc
        assert len(r.issn) == 1
        assert "1234-5678" in r.issn
        assert r.in_epmc
        assert not r.is_oa
        assert r.aam
        assert r.licence_type == "CC BY"
        assert r.licence_source == "epmc"
        assert r.journal_type == "hybrid"
        assert r.confidence == 0.8

        p = r.provenance
        assert len(p) == 2
        for by, when, note in p:
            assert by in ["richard", "wellcome"]
            assert note in ["provenance 1", "provenance 2"]

    def test_03_oagrlink(self):
        l = OAGRLink()
        l.spreadsheet_id = "1234"
        l.oagrjob_id = "9876"

        assert l.spreadsheet_id == "1234"
        assert l.oagrjob_id == "9876"

        l.save()
        time.sleep(1)

        l2 = OAGRLink.by_oagr_id("9876")

        assert l2.spreadsheet_id == "1234"
        assert l2.oagrjob_id == "9876"

    def test_04_pc_complete(self):
        job = SpreadsheetJob()
        job.save()

        # a record with no completeness
        r = Record()
        r.upload_id = job.id
        r.save()

        # a record with epmc complete
        r2 = Record()
        r2.upload_id = job.id
        r2.epmc_complete = True
        r2.save()

        # a record with both complete
        r3 = Record()
        r3.upload_id = job.id
        r3.epmc_complete = True
        r3.oag_complete = True
        r3.save()

        time.sleep(1)

        comp = job.pc_complete
        assert int(comp) == 50

        r.epmc_complete = True
        r.save()

        time.sleep(1)

        comp = job.pc_complete
        assert int(comp) == 66

        r.oag_complete = True
        r2.oag_complete = True
        r.save()
        r2.save()

        time.sleep(1)

        comp = job.pc_complete
        assert int(comp) == 100

    def test_05_duplicates(self):
        # first make ourselves a job to work on
        job = SpreadsheetJob()
        job.save()

        # now make a bunch of records, some unique and some duplicate

        # unique pmcid
        r = Record()
        r.upload_id = job.id
        r.pmcid = "PMCunique"
        r.save()

        # duplicate pmcid
        r = Record()
        r.upload_id = job.id
        r.pmcid = "PMCdupe"
        r.save()

        r = Record()
        r.upload_id = job.id
        r.pmcid = "PMCdupe"
        r.save()

        # unique pmid
        r = Record()
        r.upload_id = job.id
        r.pmid = "unique"
        r.save()

        # duplicate pmid
        r = Record()
        r.upload_id = job.id
        r.pmid = "dupe"
        r.save()

        r = Record()
        r.upload_id = job.id
        r.pmid = "dupe"
        r.save()

        # unique doi
        r = Record()
        r.upload_id = job.id
        r.doi = "10.unique"
        r.save()

        # duplicate pmcid
        r = Record()
        r.upload_id = job.id
        r.doi = "10.dupe"
        r.save()

        r = Record()
        r.upload_id = job.id
        r.doi = "10.dupe"
        r.save()

        # one that is a duplicate of everything
        r = Record()
        r.upload_id = job.id
        r.pmcid = "PMCdupe"
        r.pmid = "dupe"
        r.doi = "10.dupe"
        r.save()

        # one that is confused about its duplication
        r = Record()
        r.upload_id = job.id
        r.pmcid = "PMCdupe"
        r.pmid = "dupe"
        r.doi = "10.notdupe"
        r.save()

        time.sleep(2)

        dupes = job.list_duplicate_identifiers()

        # check the structure of the response
        assert "pmcid" in dupes
        assert "pmid" in dupes
        assert "doi" in dupes

        # check the contentes
        assert len(dupes["pmcid"]) == 1
        assert "PMCdupe" in dupes["pmcid"]
        assert len(dupes["pmid"]) == 1
        assert "dupe" in dupes["pmid"]
        assert len(dupes["doi"]) == 1
        assert "10.dupe" in dupes["doi"]