# overrides for the webapp deployment
DEBUG = True
PORT = 5017
SSL = False
THREADED = True

# important overrides for the ES module

# elasticsearch back-end connection settings
ELASTIC_SEARCH_HOST = "http://localhost:9200"
ELASTIC_SEARCH_INDEX = "wellcome"

# Classes from which to retrieve ES mappings to be used in this application
ELASTIC_SEARCH_MAPPINGS = [
    "service.dao.SpreadsheetJobDAO",
    "service.dao.RecordDAO"
]

##########################################
# service specific config

UPLOAD_DIR = "upload"