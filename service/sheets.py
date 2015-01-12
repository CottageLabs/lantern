from octopus.lib import clcsv

class MasterSheet(object):
    HEADERS = {
        u'University' : "university",
        u'PMCID' : "pmcid",
        u'PMID' : "pmid",
        u'DOI' : "doi",
        u'Publisher' : "publisher",
        u'Journal title' : "journal_title",
        u'Article title' : "article_title",
        u'Total cost of Article Processing Charge (APC), in \xa3' : "apc",
        u'Amount of APC charged to Wellcome OA grant, in \xa3 (see comment)' : "wellcome_apc",
        u'VAT charged' : "vat",
        u'COST (\xa3)' : "total_cost",
        u'Wellcome grant' : "grant_code",
        u'Licence info' : "licence_info",
        u'Notes' : "notes",

        # values used exclusively in the output
        u"Fulltext in EPMC?" : "ft_in_epmc",
        u"AAM?" : "aam",
        u"Open Access?" : "open_access",
        u"Licence" : "licence",
        u"Licence Source" : "licence_source",
        u"Journal Type" : "journal_type",
        u"Correct Article Confidence" : "confidence"
    }

    OUTPUT_ORDER = [
        "pmcid", "pmid", "doi", "article_title", "ft_in_epmc", "aam", "open_access",
        "licence", "licence_source", "journal_type", "confidence", "notes"
    ]

    def __init__(self, path=None, writer=None):
        if path is not None:
            self._sheet = clcsv.ClCsv(path)
        elif writer is not None:
            self._sheet = clcsv.ClCsv(writer=writer)
            self._set_headers()

    def _set_headers(self):
        headers = []
        for o in self.OUTPUT_ORDER:
            found = False
            for k, v in self.HEADERS.iteritems():
                if v == o:
                    headers.append(k)
                    found = True
                    break
            if not found:
                headers.append(o)
        self._sheet.set_headers(headers)

    def _header_key_map(self, key):
        for k, v in self.HEADERS.iteritems():
            if key.strip().lower() == k.lower():
                return v
        return None

    def objects(self):
        for o in self._sheet.objects():
            no = {}
            for key, val in o.iteritems():
                k = self._header_key_map(key)
                if k is not None:
                    no[k] = val
            yield no

    def add_object(self, obj):
        no = {}
        for k, v in obj.iteritems():
            for k1, v1 in self.HEADERS.iteritems():
                if k == v1:
                    no[k1] = v
                    break
        self._sheet.add_object(no)

    def save(self):
        self._sheet.save(close=False)