from service import models


def progress2json(job):
    obj = {"pc" : 0.0, "queue" : "0"}
    obj["status"] = job.status_code
    if job.status_message:
        obj["message"] = job.status_message
    if job.webhook_callback:
        obj["webhook_callback"] = job.webhook_callback

    if job.status_code == "submitted":
        obj["pc"] = 0.0
        max_ql = 10
        ql = models.SpreadsheetJob.queue_length(job.id, max=max_ql)
        obj["queue"] = ql if ql < max_ql else "{0} or more".format(max_ql + 1)
    elif job.status_code == "processing":
        obj["pc"] = float("{0:.2f}".format(job.pc_complete))
    elif job.status_code == "complete":
        obj["pc"] = 100.0

    return obj