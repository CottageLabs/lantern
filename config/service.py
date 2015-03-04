# overrides for the webapp deployment
DEBUG = True
PORT = 5017
SSL = False
THREADED = True

MAIL_FROM_ADDRESS = "sysadmin@cottagelabs.com"

# important overrides for the ES module

# elasticsearch back-end connection settings
ELASTIC_SEARCH_HOST = "http://localhost:9200"
ELASTIC_SEARCH_INDEX = "lantern"

# FIXME: shortcut for testing with OAGR
# ELASTIC_SEARCH_TEST_INDEX = "wellcome"

ELASTIC_SEARCH_VERSION = "1.4.2"

# Classes from which to retrieve ES mappings to be used in this application
ELASTIC_SEARCH_MAPPINGS = [
    "service.dao.SpreadsheetJobDAO",
    "service.dao.RecordDAO",
    "octopus.modules.oag.dao.JobsDAO",
    "service.dao.OAGRLinkDAO"
]

QUERY_ROUTE = {
    "query" : {
        "oagr" : {
            "auth" : False,
            "role" : None,
            "filters" : [],
            "dao" : "octopus.modules.oag.dao.JobsDAO"
        }
    }
}

OAGR_RUNNER_CALLBACK_CLOSURE = "service.workflow.oag_callback_closure"

# NOTE: we may want to modify these parameters in particular when we tune the running

# The combination of the following factors give the behaviour:
#
# 10 retries in the first 5 minutes, meaning rapid responses for things which are going
# to come back quickly, then every 5 minutes for 7.5 hours

# maximim number of seconds to wait between requests for identifiers, irrespective of the back-off rules
OAG_STATE_MAX_BACK_OFF = 300    # 5 minutes

# multiplier on incremental back off.  The back-off algorithm doubles the wait time each request, multiplied
# by this factor, so adjust it to speed or slow the back-off
OAG_STATE_BACK_OFF_FACTOR = 0.15    # back off slowly, so we try a lot initially

# maximum number of times to retry an identifier
OAG_STATE_MAX_RETRIES = 100  # retry pretty hard.

# you need to provide this in your local config
ROMEO_API_KEY = ""

##########################################
# service specific config

SERVICE_BASE_URL = "http://lantern.cottagelabs.com"
UPLOAD_DIR = "upload"
ALLOWED_EXTENSIONS = ['csv']
SPREADSHEET_OPTIONS = [('None', 'Type:'), ('Excel', 'Excel'), ('Google Docs', 'Google Docs'), ('Libre Office', 'Libre Office')]
OACWELLCOME_JOBS_POLL_TIME = 2  # seconds

ERROR_LOGGING_ADDRESSES = ['richard@cottagelabs.com', 'emanuil@cottagelabs.com']
