from octopus.core import initialise
from service import models, workflow
import sys, time

if __name__ == "__main__":
    initialise()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--type", help="type of identifier to run")
    parser.add_argument("-i", "--identifier", help="identifier to run through the system")
    args = parser.parse_args()

    if args.identifier is None or args.type is None:
        parser.print_help()
        exit()

    if args.type.lower() not in ["pmcid", "pmid", "doi"]:
        print "Type must be one of pmcid, pmid or doi"
        parser.print_help()
        exit()

    # we must create a job with a single record for it to be run
    job = models.SpreadsheetJob()
    job.contact_email = "test@example.com"
    job.save()

    record = models.Record()
    record.upload_id = job.id
    record.upload_pos = 1

    if args.type.lower() == "pmcid":
        record.pmcid = args.identifier
    elif args.type.lower() == "pmid":
        record.pmid = args.identifier
    elif args.type.lower() == "doi":
        record.doi = args.identifier
    record.save()

    time.sleep(2)

    oag_register = []
    msg = workflow.WorkflowMessage(job, record, oag_register)
    workflow.process_record(msg)
    workflow.process_oag(oag_register, job)

    time.sleep(2)

    i = 0
    while True:
        i += 1
        pcc = job.pc_complete
        print i, job.pc_complete, "%",
        sys.stdout.flush()
        if int(pcc) == 100:
            break
        time.sleep(2)

    out = workflow.output_csv(job)
    print out




