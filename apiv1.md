### Version 1 (deprecated 6 Dec 2015)

### Request compliance information on articles or a CSV

POST a list of articles to https://lantern.cottagelabs.com/api/compliancejob .

You can use a DOI, a PMID, a PMCID or the article's title to help the system find the article you would like to evaluate. None of these 4 pieces of identification is required, but you do need to provide at least one (empty records will be ignored silently).

If you provide any identifier as well as article title, the identifier will be used first to identify the article. If that fails, the title will be used.

If it gets down to a title match, an exact title match will be attempted in EuropePMC. If that fails to find the article, a fuzzy EPMC title match will be attempted. If that also fails to find the article, a note will be left in the article’s record on the results spreadsheet and no compliance information will be available for it.

```python
# example POST to https://lantern.cottagelabs.com/api/compliancejob
# note that /api/compliancejob/ (with trailing slash) won't work - take care to POST to endpoint above
{
    "webhook_callback": "url",  # optional
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
	
You can also include multipart/form-data POST file data with your request. E.g. with curl you would do ```curl -F "metadata=@metadata.json" -F "sheet=@/path/to/file.csv" https://lantern.cottagelabs.com/api/compliancejob``` . metadata.json would contain the webhook_callback parameter, if you wanted to supply one. Otherwise you can skip metadata.json completely and only provide a spreadsheet file as multipart/form-data .
	
In any of the cases above (JSON request, multipart/form-data with JSON and file, or just file) you will receive a redirect to a GET route detailing overall progress of the job. You can poll this URL as often as you like - it’s the GET route documented below.

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
    "status": One of ["submitted", "processing", "complete", "error"],
    "message": Will always be empty string for now. Eventually will contain human-readable details in English for developers.
}
```
	
You can hit this URL as often as you like to check on progress.
