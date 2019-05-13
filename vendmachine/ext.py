#!/usr/bin/env python3

"""External routes into server.

This will eventually house an interface for machine
configuration and maintenance.

.. note:: Routes here should require authentication.
"""

from flask import Blueprint, request, abort, make_response, render_template

from vendmachine.server import server, Status
from vendmachine.settings import settings
from vendmachine.items import Items

ext = Blueprint("ext", __name__)

@ext.route("/")
def root():
	return render_template("base.html")
