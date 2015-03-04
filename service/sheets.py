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
        u"Publisher" : "publisher",
        u"Self-Archive Preprint" : "preprint",
        u"Preprint Embargo" : "preprint_embargo",
        u"Self-Archive Postprint" : "postprint",
        u"Postprint Embargo" : "postprint_embargo",
        u"Self-Archive Publisher Version" : "publisher_print",
        u"Publisher Version Embargo" : "publisher_embargo",
        u"Compliance Processing Ouptut" : "provenance"
    }

    OUTPUT_ORDER = [
        "pmcid", "pmid", "doi", "article_title", "issn", "publisher", "in_epmc", "xml_ft_in_epmc", "aam", "open_access",
        "licence", "licence_source", "journal_type", "preprint", "preprint_embargo", "postprint", "postprint_embargo",
        "publisher_print", "publisher_embargo", "confidence", "provenance"
    ]

    DEFAULT_VALUES = {
        "aam" : "unknown",
        "licence" : "unknown"
    }
