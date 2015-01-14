from octopus.modules.es import testindex
from service import sheets
import os, csv
from StringIO import StringIO

TEST_SUBMISSION = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "resources", "test_submission.csv")

class TestImport(testindex.ESTestCase):
    def setUp(self):
        super(TestImport, self).setUp()

    def tearDown(self):
        super(TestImport, self).tearDown()

    def test_01_read(self):
        ms = sheets.MasterSheet(path=TEST_SUBMISSION)
        objects = False
        for o in ms.objects():
            objects = True
            # just check a few fields to make sure the object looks reasonable
            assert "university" in o
            assert "pmcid" in o
            assert "journal_title" in o

        assert objects

    def test_02_write_subset(self):
        # set up a very simple subset sheet
        spec = ["university", "pmcid", "journal_title"]
        s = StringIO()
        ms = sheets.MasterSheet(writer=s, spec=spec)

        # add an object which conforms to the spec of the subset
        ms.add_object({
            "university" : "A",
            "pmcid" : "a",
            "journal_title" : "1"
        })

        # check that the record has been written
        size = 0
        for o in ms.objects():
            size += 1
            assert o.get("university") == "A"
            assert o.get("pmcid") == "a"
            assert o.get("journal_title") == "1"
            assert len(o.keys()) == 3
        assert size == 1

        # now add an object with insufficient data for all columns
        ms.add_object({
            "university" : "B",
            "journal_title" : "2",
        })

        # check that the new record has been written correctly (with suitable defaults)
        size = 0
        found = False
        for o in ms.objects():
            size += 1
            if o.get("university") == "B":
                found = True
                assert o.get("journal_title") == "2"
                assert o.get("pmcid") == ""

        assert size == 2
        assert found

        # now add an object with too much data for the spec
        ms.add_object({
            "university" : "C",
            "pmcid" : "c",
            "something_else" : "Gamma"
        })

        # check that the new record has been written correctly (with suitable defaults)
        size = 0
        found = False
        for o in ms.objects():
            size += 1
            if o.get("university") == "C":
                found = True
                assert o.get("journal_title") == ""
                assert o.get("pmcid") == "c"
                assert "something_else" not in o

        assert size == 3
        assert found

    def test_03_write_full(self):
        s = StringIO()
        ms = sheets.MasterSheet(writer=s)

        # add an object which conforms to the spec of the subset
        ms.add_object({
            "university" : "A",
            "pmcid" : "a",
            "journal_title" : "1"
        })

        # check that the record has been written
        size = 0
        for o in ms.objects():
            size += 1
            assert o.get("university") == "A"
            assert o.get("pmcid") == "a"
            assert o.get("journal_title") == "1"
            assert o.get("doi") == ""
            assert len(o.keys()) == len(ms.OUTPUT_ORDER)
        assert size == 1

        # now add an object with too much data for the spec
        ms.add_object({
            "university" : "C",
            "pmcid" : "c",
            "something_else" : "Gamma"
        })

        # check that the new record has been written correctly (with suitable defaults)
        size = 0
        found = False
        for o in ms.objects():
            size += 1
            if o.get("university") == "C":
                found = True
                assert o.get("journal_title") == ""
                assert o.get("pmcid") == "c"
                assert "something_else" not in o

        assert size == 2
        assert found

    def test_04_output(self):
        # set up a very simple subset sheet (not it's not in the desired output order)
        spec = ["journal_title", "university", "pmcid"]
        s = StringIO()
        ms = sheets.MasterSheet(writer=s, spec=spec)

        # add an object which conforms to the spec of the subset
        ms.add_object({
            "university" : "A",
            "pmcid" : "a",
            "journal_title" : "1"
        })

        # output the sheet to the StringIO object
        ms.save()

        # now open the StringIO in the python standard csv reader
        s.seek(0)
        reader = csv.reader(s)
        rows = [row for row in reader]
        assert len(rows) == 2
        assert rows[0] == ["University", "PMCID", "Journal title"]
        assert rows[1] == ["A", "a", "1"]
