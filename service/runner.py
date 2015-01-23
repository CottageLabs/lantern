import sys
import time
import traceback

from octopus.lib import error_handler
from octopus.core import app, initialise
from service.workflow import process_jobs


def run():
    print "Starting OACWellcome Job Processor ... Started"
    initialise()
    error_handler.setup_error_logging(app, "OACWellcome Runner Error")
    while True:
        time.sleep(app.config.get('OACWELLCOME_JOBS_POLL_TIME', 2))
        try:
            process_jobs()
        except Exception:
            app.logger.error(traceback.format_exc())
        print ".",
        sys.stdout.flush()

if __name__ == "__main__":
    run()