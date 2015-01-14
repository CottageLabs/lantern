import sys
import time
import logging

from octopus.core import app, initialise
from service.workflow import process_jobs


def run():
    print "Starting OACWellcome Job Processor ... Started"
    initialise()
    app.logger.setLevel(logging.INFO)
    while True:
        time.sleep(app.config.get('OACWELLCOME_JOBS_POLL_TIME', 2))
        process_jobs()
        print ".",
        sys.stdout.flush()

if __name__ == "__main__":
    run()