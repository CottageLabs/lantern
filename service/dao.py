from octopus.modules.es import dao

class SpreadsheetJobDAO(dao.ESDAO):
    __type__ = 'spreadsheet'

    @classmethod
    def list_by_status(cls, status):
        q = SpreadsheetStatusQuery(status)
        return cls.object_query(q.query())

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

