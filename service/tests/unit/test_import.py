from unittest import TestCase
import os
from octopus.lib import clcsv
from service import workflow, models
from octopus.core import app, initialise

class TestImport(TestCase):
    def setUp(self):
        initialise()
        self.old_upload_dir = app.config.get("UPLOAD_DIR")
        app.config["UPLOAD_DIR"] = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "resources")

    def tearDown(self):
        app.config["UPLOAD_DIR"] = self.old_upload_dir

    def test_01_csv_reader(self):
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "resources", "test_submission.csv")
        sheet = clcsv.ClCsv(path)
        for o in sheet.objects():
            assert o is not None

    def test_02_master_sheet(self):
        pass

    def test_03_parse_csv(self):
        s = models.SpreadsheetJob()
        s.filename = "test_submission.csv"
        s.contact_email = "contact@email.com"
        s.status_code = "submitted"
        s.id = "test_submission"
        s.save()

        workflow.parse_csv(s)