from flask import Flask, request, abort, render_template, redirect, make_response, jsonify, send_file, \
    send_from_directory
from flask.views import View

from portality.core import app
from portality.lib.webapp import custom_static

@app.route("/")
def root():
    return render_template("index.html")

# this allows us to override the standard static file handling with our own dynamic version
@app.route("/static/<path:filename>")
def static(filename):
    return custom_static(filename)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


if __name__ == "__main__":
    app.run(host=app.config.get("HOST", "0.0.0.0"), debug=app.config['DEBUG'], port=app.config['PORT'])

