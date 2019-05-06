import functools

from flask import abort
from vendmachine.server import server

def get_user(request):
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

def user_access(func):
	@functools.wrap(func)
	def decorated(*args, **kwargs):
		user = get_user(request)
		if user is None or not user.authenticated():
			abort(403)
		return func(*args, **kwargs)
	return decorated

def admin_access(func):
	@functools.wrap(func)
	def decorated(*args, **kwargs):
		user = get_user(request)
		if user is None or not user.admin():
			abort(403)
		return func(*args, **kwargs)
	return decorated
