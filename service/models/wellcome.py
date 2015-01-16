from service.dao import SpreadsheetJobDAO, RecordDAO, OAGRLinkDAO
from datetime import datetime
from octopus.lib.dataobj import DataObj

class SpreadsheetJob(SpreadsheetJobDAO, DataObj):
    """
    {
        "id" : "<opaque identifier for upload>",
        "created_date" : "<date of upload of spreadsheet>",
        "filename" : "<original filename, as provided during upload>",
        "contact" : {
            "email" : "<contact email address>"
        },
        "status" : {
            "code" : "<current status of the processing job>",
            "message" : "<message for the user associated with the status>"
        }
    }
    """

    STATUS_CODES = [u"submitted", u"processing", u"complete", u"error"]

    @property
    def filename(self):
        return self._get_single("filename", self._utf8_unicode())

    @filename.setter
    def filename(self, val):
        self._set_single("filename", val, self._utf8_unicode())

    @property
    def contact_email(self):
        return self._get_single("contact.email", self._utf8_unicode())

    @contact_email.setter
    def contact_email(self, val):
        self._set_single("contact.email", val, self._utf8_unicode())

    @property
    def status_code(self):
        return self._get_single("status.code", self._utf8_unicode())

    @status_code.setter
    def status_code(self, val):
        self._set_single("status.code", val, self._utf8_unicode(), allowed_values=self.STATUS_CODES)

    @property
    def status_message(self):
        return self._get_single("status.message", self._utf8_unicode())

    @status_message.setter
    def status_message(self, val):
        self._set_single("status.message", val, self._utf8_unicode())

    def set_status(self, code, message):
        self.status_code = code
        self.status_message = message


class Record(RecordDAO, DataObj):
    """
    {
        "id" : "<opaque id of this record>",
        "created_date" : "<date this record was created>",
        "last_updated" : "<date this record was last modified>",

        "upload" : {
            "id" : "<opaque id of spreadsheet upload>",
            "pos" : "<integer: position of this record in the spreadsheet>"
        },

        "source" : {
            "university" : "<university>",
            "pmcid" : "<pmcid>",
            "pmid" : "<pmid>",
            "doi" : "<doi>",
            "publisher" : "<publisher>",
            "journal_title" : "<journal title>",
            "article_title" : "<article title>",
            "apc" : "<total cost of apc>",
            "wellcome_apc" : "<amount of apc charged to wellcome oa grant>",
            "vat" : "<vat charged>",
            "total_cost" : "<total cost>",
            "grant_code" : "<wellcome grant code>",
            "licence_info" : "<original licence information>",
            "notes" : "<original notes>"
        },

        "identifiers" : {
            "pmcid" : "<canonical form of pmcid>",
            "pmid" : "<canonical form of pmid>",
            "doi" : "<canonical form of doi>",
            "title" : "<article title>"
        },

        "supporting_info" : {
            "epmc_ft_xml" : true|false,
            "aam_from_ft_xml" : true|false,
            "aam_from_empc" : true|false,
            "issn" : ["<issn for this journal>"],
            "currently_in_oag" : true|false,
            "oag_pmcid" : "not_sent|sent|success|fto|error",
            "oag_doi" : "not_sent|sent|success|fto|error",
            "oag_pmid" : "not_sent|sent|success|fto|error",
            "epmc_complete" : true|false,
            "oag_complete" : true|false
        },

        "compliance" : {
            "in_epmc" : true|false,
            "epmc_is_oa" : true|false,
            "epmc_aam" : true|false,
            "licence" : {
                "type" : "<license type>"
            },
            "licence_source" : "epmc_xml|epmc|publisher",
            "journal_type" : "oa|hybrid",
            "confidence" : <out of 1>,
            "standard" : true|false,
            "deluxe" : true|false
        },

        "provenance" : [
            {
                "by" : "<section of the system>",
                "when" : "<datetime of when note was added>",
                "note" : "<textual description of provenance>"
            }
        ]
    }
    """

    OAG_STATES = [u"not_sent", u"sent", u"success", u"fto", u"error"]
    LICENCE_SOURCES = [u"epmc_xml", u"epmc", u"publisher"]
    JOURNAL_TYPES = [u"oa", u"hybrid"]

    @property
    def upload_id(self):
        return self._get_single("upload.id", self._utf8_unicode())

    @upload_id.setter
    def upload_id(self, val):
        self._set_single("upload.id", val, self._utf8_unicode())

    @property
    def upload_pos(self):
        return self._get_single("upload.pos", int)

    @upload_pos.setter
    def upload_pos(self, val):
        self._set_single("upload.pos", val, int)

    @property
    def source(self):
        return self._get_single("source")

    def set_source_data(self, university=None,
                                pmcid=None,
                                pmid=None,
                                doi=None,
                                publisher=None,
                                journal_title=None,
                                article_title=None,
                                apc=None,
                                wellcome_apc=None,
                                vat=None,
                                total_cost=None,
                                grant_code=None,
                                licence_info=None,
                                notes=None):
        if university is not None: self._set_single("source.university", university, self._utf8_unicode())
        if pmcid is not None: self._set_single("source.pmcid", pmcid, self._utf8_unicode())
        if pmid is not None: self._set_single("source.pmid", pmid, self._utf8_unicode())
        if doi is not None: self._set_single("source.doi", doi, self._utf8_unicode())
        if publisher is not None: self._set_single("source.publisher", publisher, self._utf8_unicode())
        if journal_title is not None: self._set_single("source.journal_title", journal_title, self._utf8_unicode())
        if article_title is not None: self._set_single("source.article_title", article_title, self._utf8_unicode())
        if apc is not None: self._set_single("source.apc", apc, self._utf8_unicode())
        if wellcome_apc is not None: self._set_single("source.wellcome_apc", wellcome_apc, self._utf8_unicode())
        if vat is not None: self._set_single("source.vat", vat, self._utf8_unicode())
        if total_cost is not None: self._set_single("source.total_cost", total_cost, self._utf8_unicode())
        if grant_code is not None: self._set_single("source.grant_code", grant_code, self._utf8_unicode())
        if licence_info is not None: self._set_single("source.licence_info", licence_info, self._utf8_unicode())
        if notes is not None: self._set_single("source.notes", notes, self._utf8_unicode())

    @property
    def pmcid(self):
        return self._get_single("identifiers.pmcid", self._utf8_unicode())

    @pmcid.setter
    def pmcid(self, val):
        self._set_single("identifiers.pmcid", val, self._utf8_unicode())

    @pmcid.deleter
    def pmcid(self):
        self._delete("identifiers.pmcid")

    @property
    def pmid(self):
        return self._get_single("identifiers.pmid", self._utf8_unicode())

    @pmid.setter
    def pmid(self, val):
        self._set_single("identifiers.pmid", val, self._utf8_unicode())

    @pmid.deleter
    def pmid(self):
        self._delete("identifiers.pmid")

    @property
    def doi(self):
        return self._get_single("identifiers.doi", self._utf8_unicode())

    @doi.setter
    def doi(self, val):
        self._set_single("identifiers.doi", val, self._utf8_unicode())

    @doi.deleter
    def doi(self):
        self._delete("identifiers.doi")

    @property
    def title(self):
        return self._get_single("identifiers.title", self._utf8_unicode())

    @title.setter
    def title(self, val):
        self._set_single("identifiers.title", val, self._utf8_unicode())

    @property
    def has_ft_xml(self):
        # return self._get_single("supporting_info.epmc_ft_xml", bool, default=False)
        return self._get_single("supporting_info.epmc_ft_xml", bool)

    @has_ft_xml.setter
    def has_ft_xml(self, val):
        self._set_single("supporting_info.epmc_ft_xml", val, bool)

    @property
    def aam_from_xml(self):
        return self._get_single("supporting_info.aam_from_ft_xml", bool, default=False)

    @aam_from_xml.setter
    def aam_from_xml(self, val):
        self._set_single("supporting_info.aam_from_ft_xml", val, bool)

    @property
    def aam_from_epmc(self):
        return self._get_single("supporting_info.aam_from_epmc", bool, default=False)

    @aam_from_epmc.setter
    def aam_from_epmc(self, val):
        self._set_single("supporting_info.aam_from_epmc", val, bool)

    @property
    def issn(self):
        return self._get_list("supporting_info.issn")

    @issn.setter
    def issn(self, val):
        self._set_list("supporting_info.issn", val, self._utf8_unicode())

    def add_issn(self, val):
        self._add_to_list("supporting_info.issn", val, self._utf8_unicode())

    @property
    def in_oag(self):
        return self._get_single("supporting_info.currently_in_oag", bool)

    @in_oag.setter
    def in_oag(self, val):
        self._set_single("supporting_info.currently_in_oag", val, bool)

    @property
    def oag_pmcid(self):
        return self._get_single("supporting_info.oag_pmcid", self._utf8_unicode())

    @oag_pmcid.setter
    def oag_pmcid(self, val):
        self._set_single("supporting_info.oag_pmcid", val, self._utf8_unicode(), allowed_values=self.OAG_STATES)

    @property
    def oag_doi(self):
        return self._get_single("supporting_info.oag_doi", self._utf8_unicode())

    @oag_doi.setter
    def oag_doi(self, val):
        self._set_single("supporting_info.oag_doi", val, self._utf8_unicode(), allowed_values=self.OAG_STATES)

    @property
    def oag_pmid(self):
        return self._get_single("supporting_info.oag_pmid", self._utf8_unicode())

    @oag_pmid.setter
    def oag_pmid(self, val):
        self._set_single("supporting_info.oag_pmid", val, self._utf8_unicode(), allowed_values=self.OAG_STATES)

    @property
    def epmc_complete(self):
        return self._get_single("supporting_info.epmc_complete", bool, default=False)

    @epmc_complete.setter
    def epmc_complete(self, val):
        self._set_single("supporting_info.epmc_complete", val, bool)

    @property
    def oag_complete(self):
        return self._get_single("supporting_info.oag_complete", bool, default=False)

    @oag_complete.setter
    def oag_complete(self, val):
        self._set_single("supporting_info.oag_complete", val, bool)

    @property
    def in_epmc(self):
        return self._get_single("compliance.in_epmc", bool)

    @in_epmc.setter
    def in_epmc(self, val):
        self._set_single("compliance.in_epmc", val, bool)
        self._calculate_compliance()

    @property
    def is_oa(self):
        return self._get_single("compliance.epmc_is_oa", bool)

    @is_oa.setter
    def is_oa(self, val):
        self._set_single("compliance.epmc_is_oa", val, bool)
        self._calculate_compliance()

    @property
    def aam(self):
        return self._get_single("compliance.epmc_aam", bool)

    @aam.setter
    def aam(self, val):
        self._set_single("compliance.epmc_aam", val, bool)
        self._calculate_compliance()

    @property
    def licence_type(self):
        return self._get_single("compliance.licence.type", self._utf8_unicode())

    @licence_type.setter
    def licence_type(self, val):
        self._set_single("compliance.licence.type", val, self._utf8_unicode())
        self._calculate_compliance()

    @licence_type.deleter
    def licence_type(self):
        self._delete("compliance.licence.type")
        self._calculate_compliance()

    @property
    def licence_source(self):
        return self._get_single("compliance.licence_source", self._utf8_unicode())

    @licence_source.setter
    def licence_source(self, val):
        self._set_single("compliance.licence_source", val, self._utf8_unicode(), allowed_values=self.LICENCE_SOURCES)
        self._calculate_compliance()

    @property
    def journal_type(self):
        return self._get_single("compliance.journal_type", self._utf8_unicode())

    @journal_type.setter
    def journal_type(self, val):
        self._set_single("compliance.journal_type", val, self._utf8_unicode(), allowed_values=self.JOURNAL_TYPES)

    @property
    def confidence(self):
        return self._get_single("compliance.confidence", float)

    @confidence.setter
    def confidence(self, val):
        self._set_single("compliance.confidence", val, float, allowed_range=(0.0, 1.0))

    @property
    def standard_compliance(self):
        return self._get_single("compliance.standard", bool, default=False)

    @standard_compliance.setter
    def standard_compliance(self, val):
        self._set_single("compliance.standard", val, bool)

    @property
    def deluxe_compliance(self):
        return self._get_single("compliance.deluxe", bool, default=False)

    @deluxe_compliance.setter
    def deluxe_compliance(self, val):
        self._set_single("compliance.deluxe", val, bool)

    @property
    def provenance(self):
        objs = self._get_list("provenance")
        return [(o.get("by"), o.get("when"), o.get("note")) for o in objs]

    def add_provenance(self, by, note, when=None):
        obj = {"by" : by, "note" : note}
        if when is None:
            when = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        obj["when"] = when

        self._add_to_list("provenance", obj)

    def _calculate_compliance(self):
        # calculate (if possible) the standard and deluxe compliance
        # Standard Compliance
        # IF full-text is in Europe PMC AND it is an author manuscript THEN compliance = YES
        # IF full-text is in Europe PMC AND the licence (in any location) is CC BY THEN compliance = YES
        #
        # Deluxe Compliance
        # IF full-text is in Europe PMC AND it is an author manuscript THEN compliance = YES
        # IF full-text is in Europe PMC AND the licence as present in Europe PMC is CC BY AND the article is in the open access subset THEN compliance = YES

        sc = False
        dc = False

        if self.in_epmc:    # minimum requirement for either kind of compliance is to be in EPMC

            if self.aam:    # if this is the AAM then this is both standard and deluxe
                sc = True
                dc = True

            if self.licence_type is not None and self.licence_type.lower().strip() in ["cc-by", "cc by"]: # if this is CC BY
                sc = True     # this is sufficient for standard compliance

                if self.licence_source is not None and self.licence_source in ["epmc_xml", "epmc"] and self.is_oa:  # for deluxe compliance licence must be known in EPMC and be in the OA subset
                    dc = True

        self.standard_compliance = sc
        self.deluxe_compliance = dc

    def prep(self):
        # ensure that both the epmc_complete and oag_complete fields are truly set
        # (this weird bit of code will ensure that they are set to their current values
        # or their default value)
        self.epmc_complete = self.epmc_complete
        self.oag_complete = self.oag_complete

        # ensure that compliance is calculated
        self._calculate_compliance()

        # ensure compliance values are set for real
        self.standard_compliance = self.standard_compliance
        self.deluxe_compliance = self.deluxe_compliance

class OAGRLink(OAGRLinkDAO, DataObj):
    @property
    def oagrjob_id(self):
        return self._get_single("oagrjob_id", self._utf8_unicode())

    @oagrjob_id.setter
    def oagrjob_id(self, val):
        self._set_single("oagrjob_id", val, self._utf8_unicode())

    @property
    def spreadsheet_id(self):
        return self._get_single("spreadsheet_id", self._utf8_unicode())

    @spreadsheet_id.setter
    def spreadsheet_id(self, val):
        self._set_single("spreadsheet_id", val, self._utf8_unicode())