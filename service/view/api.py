from flask import Blueprint
blueprint = Blueprint('api', __name__)

@blueprint.route("/compliancejob", methods=['POST'])
def compliancejob():
    return "200 OK heh"

@blueprint.route("/compliancejob/progress/<id>", methods=['GET'])
def compliancejob_progress(id):
    return "200 OK " + id