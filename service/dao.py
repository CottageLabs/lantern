from octopus.modules.es import dao

class SpreadsheetJobDAO(dao.ESDAO):
    __type__ = 'spreadsheet'

    @classmethod
    def list_by_status(cls, status):
        q = SpreadsheetStatusQuery(status)
        return cls.object_query(q.query())

    @classmethod
    def query_by_filename(cls, filename):
        return cls.object_query(terms={"filename.exact": filename})

    @property
    def pc_complete(self):
        total, epmc, oag = RecordDAO.upload_completeness(self.id)
        ec = epmc.get("T", 0.0)
        oc = oag.get("T", 0.0)
        pc = (((float(ec) + float(oc)) / 2) / float(total)) * 100.0
        return pc

class SpreadsheetStatusQuery(object):
    def __init__(self, status):
        self.status = status

    def query(self):
        return {
            "query" : {
                "term" : {"status.code.exact" : self.status}
            },
            "sort" : [{"created_date" : {"order" : "asc"}}]
        }

######################################################

class RecordDAO(dao.ESDAO):
    __type__ = "record"

    @classmethod
    def list_by_upload(cls, sheet_id, page_size=10000):
        q = RecordSheetQuery(sheet_id, page_size)
        return cls.object_query(q.query())

    @classmethod
    def get_by_identifier(cls, type, identifier):
        q = RecordIdentifierQuery(type, identifier)
        res = cls.object_query(q.query())
        if len(res) > 0:
            return res[0]
        return None

    @classmethod
    def upload_completeness(cls, upload_id):
        q = RecordsCompleteQuery(upload_id)
        res = cls.query(q=q.query())

        total = res.get("hits", {}).get("total", 0)

        epmc = {}
        for f in res.get("facets", {}).get("epmc", {}).get("terms", []):
           epmc[f.get("term")] = f.get("count", 0)

        oag = {}
        for f in res.get("facets", {}).get("oag", {}).get("terms", []):
           epmc[f.get("term")] = f.get("count", 0)

        return total, epmc, oag

class RecordIdentifierQuery(object):
    def __init__(self, type, identifier):
        self.type = type
        self.identifier = identifier

    def query(self):
        return {
            "query" : {
                "term" : {"identifiers." + self.type + ".exact" : self.identifier}
            }
        }

class RecordSheetQuery(object):
    def __init__(self, sheet_id, page_size=10000):
        self.sheet_id = sheet_id
        self.page_size = page_size

    def query(self):
        return {
            "query" : {
                "term" : {"upload.id.exact" : self.sheet_id}
            },
            "size" : self.page_size,
            "sort" : [{"upload.pos" : {"order" : "asc"}}]
        }

class RecordsCompleteQuery(object):
    def __init__(self, sheet_id):
        self.sheet_id = sheet_id

    def query(self):
        return {
            "query" : {
                "term" : {"upload.id.exact" : self.sheet_id}
            },
            "size" : 0,
            "facets" : {
                "epmc" : {"terms" : {"field" : "supporting_info.epmc_complete"}},
                "oag" : {"terms" : {"field" : "supporting_info.oag_complete"}},
            }
        }

###############################################

class OAGRLinkDAO(dao.ESDAO):
    __type__ = "oagrlink"

    @classmethod
    def by_oagr_id(cls, oagr_id):
        q = OAGRLinkQuery(oagr_id)
        res = cls.object_query(q.query())
        if len(res) > 0:
            return res[0]
        return None

class OAGRLinkQuery(object):
    def __init__(self, oagr_id):
        self.oagr_id = oagr_id

    def query(self):
        return {
            "query" : {
                "bool" :{
                    "must" : [
                        {"term" : {"oagrjob_id.exact" : self.oagr_id}}
                    ]
                }
            }
        }

