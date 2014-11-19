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
        u'Notes' : "notes"
    }

    def __init__(self, path):
        self._sheet = clcsv.ClCsv(path)

    def objects(self):
        for o in self._sheet.objects():
            no = {}
            for key, val in o.iteritems():
                no[self.HEADERS.get(key.strip())] = val
            yield no