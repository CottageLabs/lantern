from octopus.lib import clcsv

class SimpleSheet(clcsv.SheetWrapper):
    HEADERS = {
        # identifier fields to be used as input
        u'PMCID' : "pmcid",
        u'PMID' : "pmid",
        u'DOI' : "doi",
        u'Article title' : "article_title",

        # values used exclusively in the output
        u"Fulltext in EPMC?" : "in_epmc",
        u"XML Fulltext?" : "xml_ft_in_epmc",
        u"AAM?" : "aam",
        u"Open Access?" : "open_access",
        u"Licence" : "licence",
        u"Licence Source" : "licence_source",
        u"Journal Type" : "journal_type",
        u"Correct Article Confidence" : "confidence",
        u"ISSN" : "issn",
        u"Compliance Processing Ouptut" : "provenance"
    }

    OUTPUT_ORDER = [
        "pmcid", "pmid", "doi", "article_title", "issn", "in_epmc", "xml_ft_in_epmc", "aam", "open_access",
        "licence", "licence_source", "journal_type", "confidence", "provenance"
    ]

    DEFAULT_VALUES = {
        "aam" : "unknown",
        "licence" : "unknown"
    }
