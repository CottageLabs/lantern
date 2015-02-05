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
        u'Publication Date' : "publication_date",
        u'Title of paper (shortened)' : "short_title",
        u'Author(s)' : "authors",
        u'Grant References' : "grant_refs",
        u'Total cost of Article Processing Charge (APC), in \xa3' : "apc",
        u'Amount of APC charged to Wellcome OA grant, in \xa3 (see comment)' : "wellcome_apc",
        u'VAT charged' : "vat",
        u'COST (\xa3)' : "total_cost",
        u'Wellcome grant' : "grant_code",
        u'Licence info' : "licence_info",
        u'Notes' : "notes",

        # values used exclusively in the output
        u"Fulltext in EPMC?" : "in_epmc",
        u"XML Fulltext?" : "xml_ft_in_epmc",
        u"AAM?" : "aam",
        u"Open Access?" : "open_access",
        u"Licence" : "licence",
        u"Licence Source" : "licence_source",
        u"Journal Type" : "journal_type",
        u"Correct Article Confidence" : "confidence",
        u"Standard Compliance?" : "standard_compliance",
        u"Deluxe Compliance?" : "deluxe_compliance",
        u"ISSN" : "issn",
        u"Compliance Processing Ouptut" : "provenance"
    }

    OUTPUT_ORDER = [
        "university", "pmcid", "pmid", "doi", "publisher", "journal_title", "issn", "article_title", "publication_date",
        "short_title", "authors", "grant_refs", "apc", "wellcome_apc",
        "vat", "total_cost", "grant_code", "licence_info", "notes", "in_epmc", "xml_ft_in_epmc", "aam", "open_access",
        "licence", "licence_source", "journal_type", "confidence", "standard_compliance", "deluxe_compliance", "provenance"
    ]

    DEFAULT_VALUES = {
        "aam" : "unknown",
        "licence" : "unknown"
    }

    def __init__(self, path=None, writer=None, spec=None):
        if path is not None:
            self._sheet = clcsv.ClCsv(path)
        elif writer is not None:
            self._sheet = clcsv.ClCsv(writer=writer)
            self._set_headers(spec)

    def _set_headers(self, spec=None):
        headers = []

        # only write headers which are in the object spec
        if spec is not None:
            oo = [x for x in self.OUTPUT_ORDER if x in spec]
        else:
            oo = self.OUTPUT_ORDER

        # write the headers in the correct order, ensuring they exist in the
        # Master spreadsheet header definitions
        for o in oo:
            found = False
            for k, v in self.HEADERS.iteritems():
                if v == o:
                    headers.append(k)
                    found = True
                    break
            if not found:
                headers.append(o)

        # finally write the filtered, sanitised headers
        self._sheet.set_headers(headers)

    def _header_key_map(self, key):
        for k, v in self.HEADERS.iteritems():
            if key.strip().lower() == k.lower():
                return v
        return None

    def _value(self, field, value):
        if (value is None or value == "") and field in self.DEFAULT_VALUES:
            return self.DEFAULT_VALUES.get(field, "")
        return value

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
                    no[k1] = self._value(k, v)
                    break
        self._sheet.add_object(no)

    def save(self):
        self._sheet.save(close=False)