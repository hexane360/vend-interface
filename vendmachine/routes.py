#!/usr/bin/env python3

from flask import render_template, abort

from vendmachine.server import app
from vendmachine.settings import settings

@app.route("/")
def root():
    return '<html>hi</html>'

@app.route("/template")
def template():
    return render_template("base.html")
