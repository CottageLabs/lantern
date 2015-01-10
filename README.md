# Wellcome Trust OA Compliance

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
            "aam_from_epmc" : true|false,
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
    * standard - does the record meet Wellcome's standard compliance criteria
    * deluxe - does the record meet Wellcome's deluxe compliance criteria
* provenance - each operation may store information about work it did on the record.  These will later be serialised to notes on the record
    

## Upload Processing

* take the spreadsheet upload and make a record, set to status "submitted"
* attempt to open spreadsheet with csv reader.
    * if success, respond to user with successful upload message and URL
    * if failure, set status to "error" with message set (and save), and respond to user with error message

(For the time being, keep records of failed uploads, but we may choose to delete them in-line or in batches later)

## Job Processing

1. For a given spreadsheet upload (e.g. obtain by status "submitted"), set status to "processing"
2. Get all the records for that upload
3. Normalise the given identifiers and save all the records (update provenance with operations taken)
4. Obtain the EPMC metadata via the identifiers provided for each record (update provenance with method of identification, and set compliance.confidence)
5. Update the missing identifiers for each record and save
6. Obtain "in_epmc" and "epmc_is_oa" for each record from EPMC metadata and store in compliance field
7. Obtain "issn" for journal from EPMC metadata and store in supporting_info.issn (update provenance with information for user)
8. Try to obtain fulltext XML from EPMC, store success/failure in supporting_info.epmc_ft_xml (update provenance with information for user)
9. If XML FT in EPMC, determine if it is an author manuscript, store in compliance.epmc_aam and supporting_info.aam_from_ft_xml
10. If XML FT in EPMC, determine the license conditions, store in compliance.licence and compliance.license_source=epmc_xml
11. Lookup in DOAJ on ISSN or Journal Name (if no issn available), store in compliance.journal_type hybrid/oa (update provenance with action taken)
12. Build list of identifiers to send to OAG (first run) - update provenance with action taken:
    * if not supporting_info.aam_from_ft_xml AND identifiers.pmcid, use pmcid (this will try to give us the licence and AAM status); supporting_info.oag_pmcid=sent
    * if identifiers.pmcid AND not compliance.licence, use pmcid (this will try to give us the licence and AAM status); supporting_info.oag_pmcid=sent
    * if identifiers.doi AND not compliance.licence, use doi (this will try to give us the licence); supporting_info.oag_doi=sent
    * if identifiers.pmid AND not compliance.licence, use pmid (this will try to give us the licence); supporting_info.oag_pmid=sent
13. Send records for processing in OAG, await response (set supporting_info.currently_in_oag=true)
14. Process OAG responses, as they come in (set supporting_info.currently_in_oag=false) - update provenance with OAG provenance field or error details, irrespective of result:
    * if not supporting_info.aam_from_ft_xml AND identifiers.pmcid, and success, store supporting_info.aam_from_epmc and optionally compliance.licence and compliance.licence_source=epmc (if not already detected, and not FTO), set supporting_info.oag_pmcid=success|fto|error
    * if identifiers.pmcid AND not compliance.licence, and success (not FTO), store compliance.licence and compliance.licence_source=epmc, set supporting_info.oag_pmcid=success|fto|error
    * if identifiers.doi AND not compliance.licence, and success (not FTO), store compliance.licence and compliance.licence_source=publisher, set supporting_info.oag_doi=success|fto|error
    * if identifiers.pmid AND not compliance.licence, and success, store compliance.licence and compliance.licence_source=publisher, set supporting_info.oag_pmid=success|fto|error
15. Prepare to re-send FTO/error requests with different identifiers (iterate with 14 until successes or identifiers exhausted) (set supporting_info.currently_in_oag=true)
    * if pmcid request failed (supporting_info.oag_pmcid=fto|error), send doi
    * if doi request failed (supporting_info.oag_pmcid=fto|error and supporting_info.oag_doi=fto|error), send pmid
    * if pmid failed (supporting_info.oag_pmcid=fto|error and supporting_info.oag_doi=fto|error and supporting_info.oag_pmid=fto|error), store FTO or error
16. Upon final record being gathered from OAG mark spreadsheet upload status to "complete"