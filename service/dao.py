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
        if total == 0:
            # we will get a divide-by-zero error
            return 0.0    # 100% isn't right, but 0% isn't really right either
        pc = (((float(ec) + float(oc)) / 2) / float(total)) * 100.0
        return pc

    def list_duplicate_identifiers(self):
        return RecordDAO.list_duplicates(self.id)


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
    def count_by_upload(cls, sheet_id):
        q = RecordSheetQuery(sheet_id, 0)
        return cls.count(q.query())

    @classmethod
    def get_by_identifier(cls, identifier, upload, type=None):
        if type is not None:
            q = RecordTypedIdentifierQuery(identifier, type, upload)
        else:
            q = RecordUntypedIdentifierQuery(identifier, upload)
        return cls.iterate(q.query())

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
           oag[f.get("term")] = f.get("count", 0)

        return total, epmc, oag

    @classmethod
    def list_duplicates(cls, sheet_id):
        max = RecordDAO.count_by_upload(sheet_id)
        q = RecordIdentifierFacetQuery(sheet_id, max)
        res = cls.query(q.query())

        pmcids = res.get("facets", {}).get("pmcid", {}).get("terms", [])
        pmids = res.get("facets", {}).get("pmid", {}).get("terms", [])
        dois = res.get("facets", {}).get("doi", {}).get("terms", [])

        duplicates = {"pmcid" : [], "pmid" : [], "doi" : []}

        for term in pmcids:
            if term.get("count", 0) > 1:
                duplicates["pmcid"].append(term.get("term"))
            else:
                break   # Saves us a few cycles, since the array is ordered by count

        for term in pmids:
            if term.get("count", 0) > 1:
                duplicates["pmid"].append(term.get("term"))
            else:
                break   # Saves us a few cycles, since the array is ordered by count

        for term in dois:
            if term.get("count", 0) > 1:
                duplicates["doi"].append(term.get("term"))
            else:
                break   # Saves us a few cycles, since the array is ordered by count

        return duplicates

class RecordTypedIdentifierQuery(object):
    def __init__(self, identifier, type, upload):
        self.type = type
        self.identifier = identifier
        self.upload = upload

    def query(self):
        return {
            "query" : {
                "bool" :{
                    "must" : [
                        {"term" : {"identifiers." + self.type + ".exact" : self.identifier}},
                        {"term" : {"upload.id.exact" :  self.upload}}
                    ]
                }
            }
        }

class RecordUntypedIdentifierQuery(object):
    def __init__(self, identifier, upload):
        self.identifier = identifier
        self.upload = upload

    def query(self):
        return {
            "query" : {
                "bool" :{
                    "must" : [
                        {"term" : {"upload.id.exact" :  self.upload}}
                    ],
                    "should" : [
                        {"term" : {"identifiers.pmcid.exact" : self.identifier}},
                        {"term" : {"identifiers.pmid.exact" : self.identifier}},
                        {"term" : {"identifiers.doi.exact" : self.identifier}}
                    ],
                    "minimum_should_match" : 1
                }
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

class RecordIdentifierFacetQuery(object):
    def __init__(self, sheet_id, max_size=100):
        self.sheet_id = sheet_id
        self.max_size = max_size

    def query(self):
        return {
            "query": {
                "term": {"upload.id.exact": self.sheet_id}
            },
            "size": 0,
            "facets": {
                "pmcid": {
                    "terms": {
                        "field": "identifiers.pmcid.exact",
                        "size" : self.max_size
                    }
                },
                "pmid": {
                    "terms": {
                        "field": "identifiers.pmid.exact",
                        "size" : self.max_size
                    }
                },
                "doi": {
                    "terms": {
                        "field": "identifiers.doi.exact",
                        "size" : self.max_size
                    }
                }
            }
        }

###############################################

class OAGRLinkDAO(dao.ESDAO):
    __type__ = "oagrlink"

    @classmethod
    def by_oagr_id(cls, oagr_id):
        q = OAGRLinkQuery(oagr_id=oagr_id)
        res = cls.object_query(q.query())
        if len(res) > 0:
            return res[0]
        return None

    @classmethod
    def by_spreadsheet_id(cls, spreadsheet_id):
        q = OAGRLinkQuery(spreadsheet_id=spreadsheet_id)
        res = cls.object_query(q.query())
        if len(res) > 0:
            return res[0]
        return None

class OAGRLinkQuery(object):
    def __init__(self, oagr_id=None, spreadsheet_id=None):
        self.oagr_id = oagr_id
        self.spreadsheet_id = spreadsheet_id

    def query(self):
        q = {
            "query" : {
                "bool" :{
                    "must" : [

                    ]
                }
            }
        }

        if self.oagr_id is not None:
            q["query"]["bool"]["must"].append({"term" : {"oagrjob_id.exact" : self.oagr_id}})

        if self.spreadsheet_id is not None:
            q["query"]["bool"]["must"].append({"term" : {"spreadsheet_id.exact" : self.spreadsheet_id}})

        return q

