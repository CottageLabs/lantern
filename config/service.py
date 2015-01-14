# overrides for the webapp deployment
DEBUG = True
PORT = 5017
SSL = False
THREADED = True

MAIL_FROM_ADDRESS = "sysadmin@cottagelabs.com"

# important overrides for the ES module

# elasticsearch back-end connection settings
ELASTIC_SEARCH_HOST = "http://localhost:9200"
ELASTIC_SEARCH_INDEX = "wellcome"

# FIXME: shortcut for testing with OAGR
# ELASTIC_SEARCH_TEST_INDEX = "wellcome"

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

# maximim number of seconds to wait between requests for identifiers, irrespective of the back-off rules
OAG_STATE_MAX_BACK_OFF = 120

# maximum number of times to retry an identifier
OAG_STATE_MAX_RETRIES = None

##########################################
# service specific config

SERVICE_BASE_URL = "http://oacwellcome.ooz.cottagelabs.com"
UPLOAD_DIR = "upload"
ALLOWED_EXTENSIONS = ['csv']
SPREADSHEET_OPTIONS = [('None', 'Type:'), ('Excel', 'Excel'), ('Google Docs', 'Google Docs'), ('Libre Office', 'Libre Office')]
OACWELLCOME_JOBS_POLL_TIME = 2  # seconds
