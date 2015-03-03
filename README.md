# Lantern: OA Compliance

## Data Model

### Overview

There are two components to the data model:

1. The spreadsheet which has been uploaded, which is an aggregator object for
2. The records that appear in the uploaded spreadsheet

For each (1) there can be many (2), and each (2) may be associated with exactly one (1)

### Spreadsheet Upload

```json

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

```

* id - will be used as part of the opaque url for the page from which downloads can be retrieved.
* contact.email - we use a nested object here in case we later want to store additional information about the contact
* status.code - the current status of the processing being done on the spreadsheet.  Could be:
    * submitted - spreadsheet has been uploaded but processing has not yet begun
    * processing - spreadsheet processing has begun
    * complete - spreadsheet processing has completed
    * error - there was a problem reading the spreadsheet
* status.message - human readable message for the user on the state of this upload.  Particularly useful if there is an error.

### Record

```json

    {
        "id" : "<opaque id of this record>",
        "created_date" : "<date this record was created>",
        "last_updated" : "<date this record was last modified>",
        
        "upload" : {
            "id" : "<opaque id of spreadsheet upload>",
            "pos" : "<integer: position of this record in the spreadsheet>"
        },
        
        "source" : {
            "pmcid" : "<pmcid>",
            "pmid" : "<pmid>",
            "doi" : "<doi>",
            "article_title" : "<article title>",
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
            "aam_from_epmc" : true|false,
            "issn" : ["<issn for this journal>"],
            "journal" : "<name of journal>",
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
        },
        
        "provenance" : [
            {
                "by" : "<section of the system>",
                "when" : "<datetime of when note was added>",
                "note" : "<textual description of provenance>"
            }
        ]
    }
```

* upload.id - the id of the spreadsheet upload as in the first model
* upload.pos - integer position of this record in the spreadsheet, so that it can be rebuilt in the correct order when the spreadsheet is downloaded
* source - the original data provided by the spreadsheet upload, so that it can be reflected back when the spreadsheet is downloaded.  This data should not be used directly for processing purposes.  The list in this object may be extensible, and as such everything should be stored as strings to avoid mapping conflics.
* identiers.pmcid - canonicalised form of pmcid from source data (starts with "PMC" followed by the numbers)
* identifiers.pmid - canonicalised form of pmid (a number of 1 - 8 digits)
* identifiers.doi - canonicalised form of doi (starts with "10.")
* identifiers.title - title exactly as it appears in the source data
* supporting_info - this is where we'll put all status information and information to help the onward processing of the job.
    * epmc_ft_xml - is the FullText XML present in EPMC (should be the same as complaince.epmc_is_oa)
    * aam_from_ft_xml - was the AAM status detected from the EPMC XML directly
    * aam_from_epmc - was the AAM status detected from the EPMC website by OAG
    * issn - the issn(s) of the journal
    * currently_in_oag - status flag to tell us that the record is currently being processed by OAG
    * oag_pmcid - status to tell us how the processing of the PMCID went with OAG
    * oag_doi - status to tell us how the processing of the DOI went with OAG
    * oag_pmid - status to tell us how the processing of the PMID went with OAG
* compliance - the final information about the compliance of the record
    * im_epmc - EPMC metadata has the inEPMC flag set to true
    * epmc_is_oa - EPMC metadata has the isOpenAccess flat set to true
    * epmc_aam - is the content in EPMC the author manuscript
    * licence - the licence of the content, minified version of the OAG licence object
    * licence_source - where we detected the licence
    * journal_type - if the journal is OA or hybrid, as determined from the DOAJ
    * confidence - confidence that we have identified the correct journal in EPMC (will be < 1 if title match is used)
* provenance - each operation may store information about work it did on the record.  These will later be serialised to notes on the record
    

