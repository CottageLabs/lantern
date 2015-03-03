from octopus.modules.es import testindex
from service import sheets
import os, csv
from StringIO import StringIO

TEST_SUBMISSION = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "resources", "test_submission.csv")
BLANK_LINES = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "resources", "blank_rows.csv")

class TestImport(testindex.ESTestCase):
    def setUp(self):
        super(TestImport, self).setUp()

    def tearDown(self):
        super(TestImport, self).tearDown()

    def test_01_read(self):
        ms = sheets.SimpleSheet(path=TEST_SUBMISSION)
        objects = False
        for o in ms.objects():
            objects = True
            # just check a few fields to make sure the object looks reasonable
            assert "pmcid" in o
            assert "article_title" in o

        assert objects

    def test_02_write_subset(self):
        # set up a very simple subset sheet
        spec = ["article_title", "pmcid"]
        s = StringIO()
        ms = sheets.SimpleSheet(writer=s, spec=spec)

        # add an object which conforms to the spec of the subset
        ms.add_object({
            "article_title" : "A",
            "pmcid" : "a"
        })

        # check that the record has been written
        size = 0
        for o in ms.objects():
            size += 1
            assert o.get("article_title") == "A"
            assert o.get("pmcid") == "a"
            assert len(o.keys()) == 2
        assert size == 1

        # now add an object with insufficient data for all columns
        ms.add_object({
            "article_title" : "B",
        })

        # check that the new record has been written correctly (with suitable defaults)
        size = 0
        found = False
        for o in ms.objects():
            size += 1
            if o.get("article_title") == "B":
                found = True
                assert o.get("pmcid") == ""

        assert size == 2
        assert found

        # now add an object with too much data for the spec
        ms.add_object({
            "article_title" : "C",
            "pmcid" : "c",
            "something_else" : "Gamma"
        })

        # check that the new record has been written correctly (with suitable defaults)
        size = 0
        found = False
        for o in ms.objects():
            size += 1
            if o.get("article_title") == "C":
                found = True
                assert o.get("pmcid") == "c"
                assert "something_else" not in o

        assert size == 3
        assert found

    def test_03_write_full(self):
        s = StringIO()
        ms = sheets.SimpleSheet(writer=s)

        # add an object which conforms to the spec of the subset
        ms.add_object({
            "article_title" : "A",
            "pmcid" : "a",
        })

        # check that the record has been written
        size = 0
        for o in ms.objects():
            size += 1
            assert o.get("article_title") == "A"
            assert o.get("pmcid") == "a"
            assert o.get("doi") == ""
            assert len(o.keys()) == len(ms.OUTPUT_ORDER)
        assert size == 1

        # now add an object with too much data for the spec
        ms.add_object({
            "article_title" : "C",
            "pmcid" : "c",
            "something_else" : "Gamma"
        })

        # check that the new record has been written correctly (with suitable defaults)
        size = 0
        found = False
        for o in ms.objects():
            size += 1
            if o.get("article_title") == "C":
                found = True
                assert o.get("pmcid") == "c"
                assert "something_else" not in o

        assert size == 2
        assert found

    def test_04_output(self):
        # set up a very simple subset sheet (note it's not in the desired output order)
        spec = ["article_title", "doi", "pmcid"]
        s = StringIO()
        ms = sheets.SimpleSheet(writer=s, spec=spec)

        # add an object which conforms to the spec of the subset
        ms.add_object({
            "article_title" : "A",
            "pmcid" : "a",
            "doi" : "1"
        })

        # output the sheet to the StringIO object
        ms.save()

        # now open the StringIO in the python standard csv reader
        s.seek(0)
        reader = csv.reader(s)
        rows = [row for row in reader]
        assert len(rows) == 2
        assert rows[0] == ["PMCID", "DOI", "Article title"]
        assert rows[1] == ["a", "1", "A"]

    def test_05_defaults(self):
        s = StringIO()
        ms = sheets.SimpleSheet(writer=s)
        ms.add_object({
            "aam" : None,
            "licence" : "",
        })

        size = 0
        for o in ms.objects():
            size += 1
            assert o.get("aam") == "unknown"
            assert o.get("licence") == "unknown"
        assert size == 1

    def test_06_blank_rows(self):
        ms = sheets.SimpleSheet(path=BLANK_LINES)
        objects = [o for o in ms.objects()]
        assert len(objects) == 20