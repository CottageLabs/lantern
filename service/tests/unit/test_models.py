from unittest import TestCase
from service.models import Record, SpreadsheetJob

class TestModels(TestCase):
    def setUp(self): pass
    def tearDown(self): pass

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
        r.set_source_data(university="my uni",
                          pmcid="PMC12345678",
                          pmid="98765432",
                          doi="10.whatever",
                          publisher="wiley",
                          journal_title="Journal of things",
                          article_title="A study of sorts",
                          apc=100,
                          wellcome_apc=200,
                          vat=20,
                          total_cost=300,
                          grant_code="WELL01",
                          licence_info="CC BY",
                          notes="this is a note")
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
        r.standard_compliance = True
        r.deluxe_compliance = False
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
        assert r.standard_compliance
        assert not r.deluxe_compliance

        p = r.provenance
        assert len(p) == 2
        for by, when, note in p:
            assert by in ["richard", "wellcome"]
            assert note in ["provenance 1", "provenance 2"]



