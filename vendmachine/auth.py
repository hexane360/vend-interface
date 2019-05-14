#!/usr/bin/env python3

"""Functions to handle Flask authentication.

Incomplete at the moment. Took a lot of inspiration from OctoPrint.
"""

import functools

from flask import abort, request
from flask_login import current_user, login_fresh

from vendmachine.server import server

from vendmachine.users import api_user, anon_user
server.login_manager.anonymous_user = anon_user

@server.login_manager.user_loader
def load_user(uid):
	return server.users.get(uid)

@server.login_manager.request_loader
def get_user(request):
	"""Try to extract a user from a Flask request.
	
	Looks for a valid api key in headers, post data, or query strings.
	"""
	apikey = None
	if hasattr(request, "values") and "apikey" in request.values:
		apikey = request.values["apikey"]
	elif "X-Api-Key" in request.headers.keys():
		apikey = request.headers.get("X-Api-Key")
	if apikey is not None:
		if apikey == settings().get(["access", "apikey"]): #global apikey
			return api_user
		return server.users.find_one(apikey=apikey)
	return None

def is_user(request):
	"""Validate a user given a Flask request."""
	return current_user.is_authenticated
	#user = get_user(request)
	#return user is not None and user.authenticated()

def is_admin(request):
	"""Validate an administrator given a Flask request."""
	return current_user.is_admin
	#user = get_user(request)
	#return user is not None and user.admin()

def is_fresh(request):
	return current_user.is_fresh()

def is_ext(request):
	"""Determines whether a request came from outside (/ext/)."""
	return request.path.startswith('/ext/')

def make_access_decorator(cond, doc="Validate before running a Flask route/handler."):
	"""Generic access decorator. Provides access only if cond(request) is truthy."""
	def decorator(func):
		@functools.wraps(func)
		def decorated(*args, **kwargs):
			if request.method == "OPTIONS": #OPTIONS requests exempt from login
				return func(*args, **kwargs)
			if cond(request): #cond supplied to make_access_decorator
				return func(*args, **kwargs)
			return server.login_manager.unauthorized()
		return decorated
	decorator.__doc__ = doc
	return decorator

user_access = make_access_decorator(lambda r: current_user.is_authenticated, """
Validate a user before running a Flask route/handler.

Used as a decorator.""")

admin_access = make_access_decorator(lambda r: current_user.is_admin, """
Validate an admin before running a Flask route/handler.

Used as a decorator.""")

fresh_user_access = make_access_decorator(lambda r: current_user.is_authenticated and login_fresh(),
"""Validate a user, requiring a fresh login.""")

fresh_admin_access = make_access_decorator(lambda r: current_user.is_admin and login_fresh(),
"""Validate an admin, requiring a fresh login.""")

ext_user_access = make_access_decorator(lambda r: not is_ext(r) or current_user.is_authenticated, """
Validate a user if request happened from outside (/ext/).""")

ext_admin_access = make_access_decorator(lambda r: not is_ext(r) or current_user.is_admin, """
Validate an admin if request happened from outside (/ext/).""")

ext_read_access = make_access_decorator(lambda r: not is_ext(r) or current_user.is_authenticated or not server.config.get(['access', 'restrict_read']), """
Validate that an external client is allowed to read APIs. This requires authentication if set in configuration.""")

ext_write_access = make_access_decorator(lambda r: not is_ext(r) or current_user.is_authenticated or not server.config.get(['access', 'restrict_write']), """
Validate that an external client is allowed to write to APIs. This requires authentication if set in configuration.""")

read_access = make_access_decorator(lambda r: current_user.is_authenticated or not server.config.get(['access', 'restrict_read']), """
Validate that a client is allowed to view pages. This requires authentication if set in configuration.""")
