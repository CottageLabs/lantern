# Lantern: OA Compliance

## API

### Version 2 (current, released 6 Dec 2015)

### Request compliance information on articles or a CSV

POST a list of articles to https://lantern.cottagelabs.com/api/compliancejob .

You can use a DOI, a PMID, a PMCID or the article's title to help the system find the article you would like to evaluate. None of these 4 pieces of identification is required, but you do need to provide at least one (empty records will be ignored silently).

If you provide any identifier as well as article title, the identifier will be used first to identify the article. If that fails, the title will be used.

If it gets down to a title match, an exact title match will be attempted in EuropePMC. If that fails to find the article, a fuzzy EPMC title match will be attempted. If that also fails to find the article, a note will be left in the article’s record on the results spreadsheet and no compliance information will be available for it.

```python
# example POST to https://lantern.cottagelabs.com/api/compliancejob
# note that /api/compliancejob/ (with trailing slash) won't work - take care to POST to endpoint above
{
    "webhook_callback": "http://your_url",  # optional
    "articles": [
        {
            "doi":"10.1/doi",
            "pmid": "123456",
            "pmcid": "PMC123456",
            "title":"Article Title 1"
        },
        {
            "doi":"10.2/doi"
        }
    ]
}
```

You can also include multipart/form-data POST file data with your request. E.g. with curl you would do ```curl -X POST -H "application/json" -d '{"webhook_callback": "http://your_url"}' -F "file=@/path/to/file.csv" https://lantern.cottagelabs.com/api/compliancejob``` . The filename ("file" in the preceding example) does not matter, the API will just process the first file you submit.
	
Either way (JSON request or multipart/form-data with JSON + file) you will receive 200 OK response detailing where to poll for progress The format of the response is the same as the format of the GET /api/compliancejob/progress/:id below. You can poll this URL as often as you like.

The webhook_callback will be hit with a GET request when all your articles have finished processing, so pass any parameters you need to give to your service straight in the URL.

### Check on the progress of a compliance job

GET information on a compliance job ```https://lantern.cottagelabs.com/api/compliancejob/progress/:id``` . This will return JSON in this format:
    
```python
# example response to a GET request to check on progress
{
    "progress_url": https://lantern.cottagelabs.com/api/compliancejob/progress/:id,
    "pc": Float (0.0 to 100.0), rounded to 2 decimal places,
    "queue": Any number between 0 and 10, or the string "11 or more",
    "results_url": https://lantern.cottagelabs.com/download_progress/:id,
    "status": One of ["submitted", "processing", "complete", "error"]
}
```
	
You can hit this URL as often as you like to check on progress.


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
            "publisher" : "<name of publisher>",
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
            "in_core" : true|false,
            "journal_embargo" : {
                "preprint" : "<preprint embargo>",
                "postprint" : "<postprint embargo>",
                "publisher" : "<publisher's final copy embargo>"
            },
            "journal_self_archiving : {
                "preprint" : "<preprint self archiving>",
                "postprint" : "<postprint self archiving>",
                "publisher" : "<publisher's final self archiving>"
            }
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
    

