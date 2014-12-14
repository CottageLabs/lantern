from unittest import TestCase
from octopus.core import initialise
from service import workflow, models

PMCID_SUCCESS = "PMC4219345"
PMCID_SUCCESS_TITLE = "BORIS/CTCFL is an RNA-binding protein that associates with polysomes."
PMCID_SUCCESS_FT_TITLE = "BORIS/CTCFL is an RNA-binding protein that associates with polysomes"

PMCID_ERROR = "PMC00000000"

PMID_SUCCESS = "24279897"
PMID_SUCCESS_TITLE = "BORIS/CTCFL is an RNA-binding protein that associates with polysomes."

PMID_ERROR = "0000000"

DOI_SUCCESS = "10.1186/1471-2121-14-52"
DOI_SUCCESS_TITLE = "BORIS/CTCFL is an RNA-binding protein that associates with polysomes."

DOI_ERROR = "10.1234"

EXACT_TITLE = "BORIS/CTCFL is an RNA-binding protein that associates with polysomes."
EXACT_TITLE_PMCID = "PMC4219345"

FUZZY_TITLE = "BORIS an RNA-binding protein with polysomes."
FUZZY_TITLE_PMCID = "PMC4219345"

TITLE_ERROR = "Denaturalize ectype lawing kvas prothalamion. Perennial predivided aristoteles detachedly lactobacilli. Meagerly subruler recodification nonreprisal crinogenic."

class TestWorkflow(TestCase):
    def setUp(self):
        initialise()

    def tearDown(self):
        pass

    def test_01_get_epmc_metadata(self):
        record = models.Record()

        # an empty record, shoud result in a failure
        msg = workflow.WorkflowMessage(record=record)
        md, conf = workflow.get_epmc_md(msg)
        assert md is None
        assert conf is None

        # contains a pmcid that yields a result
        record.pmcid = PMCID_SUCCESS
        msg = workflow.WorkflowMessage(record=record)
        md, conf = workflow.get_epmc_md(msg)
        assert md is not None
        assert md.title == PMCID_SUCCESS_TITLE
        assert conf == 1.0

        # contains a pmcid that does not yeild a result
        record.pmcid = PMCID_ERROR
        msg = workflow.WorkflowMessage(record=record)
        md, conf = workflow.get_epmc_md(msg)
        assert md is None
        assert conf is None

        # contains invalid pmcid and valid pmid
        record.pmcid = PMCID_ERROR
        record.pmid = PMID_SUCCESS
        msg = workflow.WorkflowMessage(record=record)
        md, conf = workflow.get_epmc_md(msg)
        assert md is not None
        assert md.title == PMID_SUCCESS_TITLE
        assert conf == 1.0

        # contains an invalid pmid only
        del record.pmcid
        record.pmid = PMID_ERROR
        msg = workflow.WorkflowMessage(record=record)
        md, conf = workflow.get_epmc_md(msg)
        assert md is None
        assert conf is None

        # invalid pmid and valid doi
        record.pmid = PMID_ERROR
        record.doi = DOI_SUCCESS
        msg = workflow.WorkflowMessage(record=record)
        md, conf = workflow.get_epmc_md(msg)
        assert md is not None
        assert md.title == DOI_SUCCESS_TITLE
        assert conf == 1.0

        # contains invalid doi only
        del record.pmid
        record.doi = DOI_ERROR
        msg = workflow.WorkflowMessage(record=record)
        md, conf = workflow.get_epmc_md(msg)
        assert md is None
        assert conf is None

        # contains an invalid doi and a title which can be matched exactly
        record.doi = DOI_ERROR
        record.title = EXACT_TITLE
        msg = workflow.WorkflowMessage(record=record)
        md, conf = workflow.get_epmc_md(msg)
        assert md is not None
        assert md.pmcid == EXACT_TITLE_PMCID
        assert conf < 1.0

        # contains a title that can be matched fuzzily
        del record.doi
        record.title = FUZZY_TITLE
        msg = workflow.WorkflowMessage(record=record)
        md, conf = workflow.get_epmc_md(msg)
        assert md is not None
        assert md.pmcid == FUZZY_TITLE_PMCID
        assert conf < 1.0

        # contains a title that can't be matched in any way
        record.title = TITLE_ERROR
        msg = workflow.WorkflowMessage(record=record)
        md, conf = workflow.get_epmc_md(msg)
        assert md is None
        assert conf is None

    def test_02_get_fulltext_xml(self):
        record = models.Record()
        msg = workflow.WorkflowMessage(record=record)

        # a successful fulltext retrieval
        record.pmcid = PMCID_SUCCESS
        ft = workflow.get_epmc_fulltext(msg)
        assert ft is not None
        assert ft.title == PMCID_SUCCESS_FT_TITLE, ft.title

        # failed fulltext retrieval
        record.pmcid = PMCID_ERROR
        ft = workflow.get_epmc_fulltext(msg)
        assert ft is None

    def test_03_doaj(self):
        record = models.Record()
        msg = workflow.WorkflowMessage(record=record)

        # An OA journal
        record.issn = "1338-3973"
        is_oa = workflow.doaj_lookup(msg)
        assert is_oa is True

        # a journal that we invented
        record.issn = "1234-5678"
        is_oa = workflow.doaj_lookup(msg)
        assert is_oa is False