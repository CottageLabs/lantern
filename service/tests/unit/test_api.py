import os
import logging
from uuid import uuid1
import requests
from simplejson import JSONDecodeError
from time import sleep

from octopus.core import app
from octopus.modules.es import testindex
from octopus.modules.test.helpers import get_first_free_port, TestServer, diff_dicts
from service import models, workflow, web


class TestApi(testindex.ESTestCase):
    def setUp(self):
        super(TestApi, self).setUp()
        self.port = get_first_free_port()
        self.test_server = TestServer(port=self.port, index=app.config['ELASTIC_SEARCH_INDEX'], python_app_module_path=os.path.abspath(web.__file__))
        self.test_server.spawn()
        self.appurl = self.test_server.get_server_url()

        self.apibase = self.appurl + '/api'

    def tearDown(self):
        super(TestApi, self).tearDown()
        self.test_server.terminate()

    # def test_01_get_progress(self):
    #     job = workflow.make_spreadsheet_job('test task ' + uuid1().hex, "test@example.org")
    #     job.save()
    #     sleep(1)
    #     progress_url = self.apibase + '/compliancejob/progress/{0}'.format(job.id)
    #     expected_results = {
    #         "progress_url": progress_url,
    #         "pc": 0.0,
    #         "queue": 0,
    #         "results_url": self.apibase + '/download_progress/{0}'.format(job.id),
    #         "status": "submitted",
    #         "message": ""
    #     }
    #
    #     r = requests.get(progress_url)
    #     assert r.status_code == requests.codes.ok
    #     try:
    #         results = r.json()
    #     except JSONDecodeError:
    #         self.fail("The API did not return a JSON response as expected.")
    #
    #     assert expected_results == results, diff_dicts(expected_results, results, d1_label="Expected results", d2_label="Actual results")

    # def test_02_create_job(self):
    #     pass
