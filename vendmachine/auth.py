#!/usr/bin/env python3

"""Functions to handle Flask authentication.

Incomplete at the moment. Took a lot of inspiration from OctoPrint.
"""

import functools

from flask import abort, request
from vendmachine.server import server

def get_user(request):
	"""Try to extract a user from a Flask request.
	
	Looks for a valid api key in headers, post data, or query strings.
	"""
	apikey = None
	if hasattr(request, "values") and "apikey" in request.values:
		apikey = request.values["apikey"]
	if "X-Api-Key" in request.headers.keys():
		return request.headers.get("X-Api-Key")
	if apikey is not None:
		if apikey == settings().get(["server", "apikey"]): #global apikey
			return server.users.apiuser
		return server.users.find_one(apikey=apikey)
	return None

def is_user(request):
	"""Validate a user given a Flask request."""
	user = get_user(request)
	if user is None or not user.authenticated():
		return False
	return True

def is_admin(request):
	"""Validate an administrator given a Flask request."""
	user = get_admin(request)
	if user is None or not user.admin():
		return False
	return True

def user_access(func):
	"""Validate a user before running a Flask route/handler.
	
	Used as a decorator."""
	@functools.wraps(func)
	def decorated(*args, **kwargs):
		if not is_user(request):
			abort(403)
		return func(*args, **kwargs)
	return decorated

def admin_access(func):
	"""Validate an admin before running a Flask route/handler.
	
	Used as a decorator."""
	@functools.wraps(func)
	def decorated(*args, **kwargs):
		if not is_admin(request):
			abort(403)
		return func(*args, **kwargs)
	return decorated

def ext_user_access(func):
	"""Validate a user if request happened from outside (/ext/).
	
	Used as a decorator."""
	@functools.wraps(func)
	def decorated(*args, **kwargs):
		if request.path.startswith('/ext/') and not is_user(request):
			abort(403)
		return func(*args, **kwargs)
	return decorated

def ext_admin_access(func):
	"""Validate an admin if request happened from outside (/ext/).
	
	Used as a decorator."""
	@functools.wraps(func)
	def decorated(*args, **kwargs):
		if request.path.startswith('/ext/') and not is_admin(request):
			abort(403)
		return func(*args, **kwargs)
	return decorated
