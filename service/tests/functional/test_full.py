from octopus.modules.es import testindex
from octopus.core import app
from service import workflow
import codecs, os, time

TEST_SUBMISSION = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "resources", "test_submission.csv")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "resources", "tmpupload")

# Note, we have a couple of options here, just pick whichever one you want to work with
# See the resources directory for alternatives
# FULL_SUBMISSION = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "resources", "test_submission.csv")
# FULL_SUBMISSION = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "resources", "apc_2012_2013.csv")
FULL_SUBMISSION = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "resources", "compliance_pubmed_mar14.csv")


class FileHandle(object):
    def __init__(self, content):
        self.content = content

    def save(self, path):
        with codecs.open(path, "wb") as out:
            out.write(self.content)

class TestWorkflow(testindex.ESTestCase):
    def setUp(self):
        super(TestWorkflow, self).setUp()
        self.old_upload_dir = app.config.get("UPLOAD_DIR")
        if not os.path.exists(UPLOAD_DIR):
            os.mkdir(UPLOAD_DIR)
        app.config["UPLOAD_DIR"] = UPLOAD_DIR

    def tearDown(self):
        # FIXME: for the moment this test doesn't tear down, because we're interested in
        # dissecting the results
        # super(TestWorkflow, self).tearDown()
        app.config["UPLOAD_DIR"] = self.old_upload_dir

    def test_01_full_synchronous(self):
        # first pretend to do the file upload, using the test submission
        fh = FileHandle(open(TEST_SUBMISSION, "r").read())
        job = workflow.csv_upload(fh, "test_submission.csv", "contact@email.com")
        time.sleep(2)

        # now call the overall job processor
        workflow.process_jobs()

        # once the job processor is finished, we can export the csv for the job we ran
        csvcontent = workflow.output_csv(job)
        with codecs.open(os.path.join(UPLOAD_DIR, "output.csv"), "wb") as f:
            f.write(csvcontent)

    def test_02_full_asynchronous(self):
        # first pretend to do the file upload, using the test submission
        fh = FileHandle(open(FULL_SUBMISSION, "r").read())
        job = workflow.csv_upload(fh, "full_submission.csv", "contact@email.com")
        time.sleep(2)

        # now call the overall job processor
        workflow.process_jobs()

        # once the job processor returns, we must monitor the job itself for completeness
        for i in range(100):
            pc = job.pc_complete
            print i, pc
            if int(pc) == 100:
                break
            time.sleep(2)

        # once the job processor is finished, we can export the csv for the job we ran
        csvcontent = workflow.output_csv(job)
        with codecs.open(os.path.join(UPLOAD_DIR, "output.csv"), "wb", "utf8") as f:
            f.write(csvcontent)


