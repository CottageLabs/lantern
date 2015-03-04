from octopus.modules.es import testindex
from service import models, workflow
from datetime import datetime
import csv
from StringIO import StringIO

class TestImport(testindex.ESTestCase):
    def setUp(self):
        super(TestImport, self).setUp()

    def tearDown(self):
        super(TestImport, self).tearDown()

    def test_01_export(self):
        # make a job - we don't much care about its content for this test
        job = models.SpreadsheetJob()
        job.save()

        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        # make a few records for it

        # all fields filled in correctly
        r1 = models.Record()
        r1.pmcid = "PMC1234"
        r1.pmid = "1234"
        r1.doi = "10.1234"
        r1.title = "The Title"
        r1.has_ft_xml = True
        r1.in_epmc = True
        r1.aam = True
        r1.is_oa = True
        r1.licence_type = "CC0"
        r1.licence_source = "publisher"
        r1.journal_type = "hybrid"
        r1.confidence = 0.9
        r1.add_provenance("test", "provenance", now)
        r1.upload_id = job.id
        r1.upload_pos = 1
        r1.issn = ["1234-5678", "9876-5432"]
        r1.publisher = "The Publisher"
        r1.preprint_self_archive = "can"
        r1.journal_preprint_embargo = "12 months"
        r1.postprint_self_archive = "cannot"
        r1.journal_postprint_embargo = "100 years"
        r1.publisher_self_archive = "can"
        r1.journal_publisher_embargo = "6 months"
        r1.save()

        r2 = models.Record()
        r2.pmcid = "PMC9876"
        r2.upload_id = job.id
        r2.upload_pos = 2
        r2.save()

        r3 = models.Record()
        r3.pmid = "9876"
        r3.upload_id = job.id
        r3.upload_pos = 3
        r3.title = None
        r3.licence_type = ""
        r3.add_provenance("test", "provenance", now)
        r3.add_provenance("test", "more", now)
        r3.save()


        # refresh the index ready for querying
        models.SpreadsheetJob.refresh()
        models.Record.refresh()

        out = workflow.output_csv(job)

        s = StringIO(out)
        reader = csv.reader(s)
        rows = [r for r in reader]

        assert len(rows) == 4
        assert rows[0] == [
            'PMCID', 'PMID', 'DOI', 'Article title',
            "ISSN", "Publisher", "Fulltext in EPMC?", 'XML Fulltext?', 'AAM?',
            'Open Access?', 'Licence', 'Licence Source', 'Journal Type',
            "Self-Archive Preprint", "Preprint Embargo", "Self-Archive Postprint", "Postprint Embargo",
            "Self-Archive Publisher Version", "Publisher Version Embargo",
            'Correct Article Confidence', 'Compliance Processing Ouptut'
        ]
        assert rows[1] == [
            'PMC1234', '1234', '10.1234', 'The Title',
            "1234-5678, 9876-5432", "The Publisher", "True", 'True', 'True',
            'True', 'CC0', 'publisher', 'hybrid',
            "can", "12 months", "cannot", "100 years",
            "can", "6 months",
            '0.9', '[' + now + ' test] provenance'
        ]
        assert rows[2] == [
            "PMC9876", "", "", "",
            "", "", "", "", "unknown",
            "", "unknown", "", "",
            "", "", "", "",
            "", "",
            "", ""
        ]
        assert rows[3] == [
            "", "9876", "", "",
            "", "", "", "", "unknown",
            "", "unknown", "", "",
            "", "", "", "",
            "", "",
            "", '[' + now + ' test] provenance\n\n[' + now + ' test] more']




