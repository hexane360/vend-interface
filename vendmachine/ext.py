#!/usr/bin/env python3

"""External routes into server.

This will eventually house an interface for machine
configuration and maintenance.

.. note:: Routes here should require authentication.
"""

from urllib.parse import urlparse, urljoin

import flask
from flask import Blueprint, request, abort, redirect
from flask import make_response, render_template, url_for
from flask_login import login_user, logout_user, current_user

from vendmachine.server import server, Status
from vendmachine.config import config
from vendmachine.auth import user_access, admin_access, read_access

ext = Blueprint("ext", __name__)

@ext.route("/")
@read_access
def root():
	return render_template("ext.html")

@ext.route("/admin")
@admin_access
def admin():
	return "admin zone", 200

@ext.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html')
	else:
		if not request.values:
			abort(400)
		if 'username' not in request.values:
			abort(400)
		if 'password' not in request.values:
			abort(400)
		user = server.users.get(request.values['username'])
		if not user:
			flask.flash("User {} does not exist".format(request.values['username']))
			return render_template('login.html')
		if not user.check_pass(request.values['password']):
			flask.flash("Invalid password")
			return render_template('login.html')
		remember = False
		if request.values and 'remember' in request.values:
			remember = request.values['remember']
		print("Logging in user '{}'".format(user.get_id()))
		login_user(user, remember=remember)
		flask.flash("Logged in successfully.")
		
		next = flask.request.values.get('next')
		if not is_safe_url(next):
			abort(400)
		return redirect(next or "/ext")

server.login_manager.login_view = "ext.login"

@ext.route("/logout")
@user_access
def logout():
	print("Logging out user '{}'".format(current_user.get_id()))
	logout_user()
	flask.flash("Logged out successfully.") #probably want to replace with more client-side, AJAX-like stuff
	return redirect('/ext/login')

def is_safe_url(target):
	ref_url = urlparse(request.host_url)
	test_url = urlparse(urljoin(request.host_url, target))
	return test_url.scheme in ('http', 'https') and \
	       ref_url.netloc == test_url.netloc
