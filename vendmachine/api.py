#!/usr/bin/env python3

"""Main API for all clients.

"""

from flask import Blueprint, request, jsonify, abort, make_response, url_for
import json
import functools

from vendmachine.server import server, Status
from vendmachine.config import config
from vendmachine.auth import ext_read_access, ext_write_access, ext_admin_access

api = Blueprint("api", __name__)

def onRegister(setup_state):
	"""Handles the registration of an API Blueprint.
	
	Doesn't do much currently.
	"""
	blueprint = setup_state.blueprint
	#if setup_state.options.get('auth') == True:
	if setup_state.url_prefix.startswith('/ext/'): #not really used right now
		#inside here, 'route' works but not 'before_request'
		#maybe use to register authentication-specific routes?
		print("Authenticated API on {}".format(setup_state.url_prefix))

api.record(onRegister)

@api.route("/", methods=['GET'])
@ext_read_access
def api_root():
	"""Return all available API endpoints in a map.
	
	Requires read access.
	"""
	return jsonify({
		"/": ['GET'],
		"/status": ['GET'],
		"/refresh": ['GET'],
		"/credit": ['GET', 'PUT', 'PATCH'],
		"/items": ['GET', 'POST'],
		"/items/<string:name>": ['GET', 'PUT', 'PATCH', 'DELETE'],
		"/items/<string:name>/price": ['GET'],
		"/channels": ['GET', 'POST'],
		"/channels/<int:channel>": ['GET', 'PUT', 'PATCH', 'DELETE'],
		"/channels/<int:channel>/price": ['GET'],
		"/channels/<int:channel>/vend": ['POST'],
		"/vend": ['POST'],
	})

@api.route("/status", methods=['GET'])
@ext_read_access
def status(code=200):
	"""Return the machine status, as defined in `Server.status_data()`.
	
	Requires read access.
	"""
	return jsonify(server.status_data()), code

@api.route("/refresh", methods=['POST'])
@ext_admin_access
def refresh():
	"""Ask all websocket clients to refresh themselves.
	
	Requires admin access.
	"""
	socketio.emit('refresh')
	return status()

@api.route("/credit", methods=['GET'])
@ext_read_access
def get_credit():
	return jsonify({"credit": server.credit()}), 200

@api.route("/credit", methods=['PUT'])
@ext_write_access
def set_credit():
	amount = try_arg(request, 'amount', float)
	server.set_credit(amount)
	return status()

@api.route("/credit", methods=['PATCH'])
@ext_write_access
def add_credit():
	amount = try_arg(request, 'amount', float)
	server.add_credit(amount)
	return status()

@api.route("/items", methods=['GET'])
@ext_read_access
def get_items():
	return jsonify({"items": server.items.items()})

@api.route("/items", methods=['POST'])
@ext_write_access
def add_item():
	if not request.values:
		error("Missing arguments")
	name = try_arg(request, 'name', str)
	headers = {'Location': url_for("api.get_item", name=name)}
	try:
		if name in server.items.items(): #item already exists
			return jsonify({"item": server.items.get_item(name)}), 400, headers
		else:
			price = try_arg(request, 'price', float)
			server.items.add_item(**request.values)
	except ValueError as e:
		error(str(e))
	return jsonify({"item": server.items.get_item(name)}), 201, headers

@api.route("/items/<string:name>", methods=['GET'])
@ext_read_access
def get_item(name):
	item = server.items.get_item(name)
	if item is None:
		error("Item does not exist")
	return jsonify({"item": item}), 200

@api.route("/items/<string:name>", methods=['PUT'])
@ext_write_access
def replace_item(name):
	if not request.values:
		error("Missing arguments")
	try:
		price = try_arg(request, 'price', float)
		if name in server.items.items():
			server.items.replace_item(name, **request.values)
			code = 200
		else:
			server.items.add_item(name, **request.values)
			code = 201
	except ValueError as e:
		error(str(e))
	return jsonify({"item": server.items.get_item(name)}), code

@api.route("/items/<string:name>", methods=['PATCH'])
@ext_write_access
def update_item(name):
	if not request.values:
		error("Missing arguments")
	try:
		if name in server.items.items():
			server.items.update_item(name, **request.values)
			code = 200
		else:
			price = try_arg(request, 'price', float)
			server.items.add_item(name, **request.values)
			code = 201
	except ValueError as e:
		error(str(e))
	return jsonify({"item": server.items.get_item(name)}), code

@api.route("/items/<string:name>", methods=['DELETE'])
@ext_write_access
def delete_item(name):
	if name not in server.items.items():
		error("Item does not exist", 404)
	try:
		server.items.del_item(name)
	except ValueError as e:
		error(str(e))
	return "", 204

@api.route("/items/<string:name>/price", methods=['GET'])
@ext_read_access
def get_item_price(name):
	item = server.items.get_item(name)
	if item is None:
		error("Item does not exist", 404)
	price = item['price']
	return jsonify({"price": price, "text": "${:,.2f}".format(price)})

@api.route("/channels", methods=['GET'])
@ext_read_access
def get_channels():
	return jsonify({"channels": server.items.channels()})

@api.route("/channels", methods=['POST'])
@ext_write_access
def add_channel():
	if not request.values:
		error("Missing arguments")
	channel = try_arg(request, "channel", int)
	if channel < 0 or channel > 99:
		error("Invalid channel")
	headers = {'Location': url_for("api.get_channel", channel=channel)}
	if channel in server.items.channels():
		return jsonify({"channel": server.items.get_channel(channel)}), 400, headers
	motor = try_arg(request, "motor", int)
	item = try_arg(request, "item")
	qty = request.values.get("qty")
	try:
		server.items.add_channel(channel, motor, item, qty)
	except ValueError as e:
		error(str(e))
	return jsonify({"channel": server.items.get_channel(channel)}), 201, headers

@api.route("/channels/<int:channel>", methods=['GET'])
@ext_read_access
def get_channel(channel):
	if channel not in server.items.channels():
		error("Channel does not exist", 404)
	return jsonify({"channel": server.items.get_channel(channel)}), 200

@api.route("/channels/<int:channel>", methods=['PUT'])
@ext_write_access
def replace_channel(channel):
	if not request.values:
		error("Missing arguments")
	if channel not in server.items.channels():
		error("Channel does not exist", 404)
	motor = try_arg(request, "motor", int)
	item = try_arg(request, "item")
	qty = request.values.get("qty")
	try:
		if name in server.items.items():
			server.items.replace_channel(channel, motor, item, qty)
			code = 200
		else:
			server.items.add_channel(channel, motor, item, qty)
			code = 201
	except ValueError as e:
		error(str(e))
	return jsonify({"channel": server.items.get_channel(channel)}), code

@api.route("/channels/<int:channel>", methods=['PATCH'])
@ext_write_access
def update_channel(channel):
	if not request.values:
		error("Missing arguments")
	if channel not in server.items.channels():
		error("Channel does not exist", 404)
	motor = request.values.get("motor")
	item = request.values.get("item")
	qty = request.values.get("qty")
	try:
		server.items.update_channel(channel, motor, item, qty)
	except ValueError as e:
		error(str(e))
	return jsonify({"channel": server.items.get_channel(channel)}), 200

@api.route("/channels/<int:channel>", methods=['DELETE'])
@ext_write_access
def delete_channel(channel):
	if channel not in server.items.channels():
		error("Channel does not exist", 404)
	try:
		server.items.del_channel(channel)
	except ValueError as e:
		error(str(e))
	return "", 204

@api.route("/channels/<int:channel>/price", methods=['GET'])
@ext_read_access
def get_channel_price(channel):
	if channel not in server.items.channels():
		error("Channel does not exist", 404)
	price = server.items.get_item(channel=channel)['price']
	return jsonify({"price": price, "text": "${:,.2f}".format(price)})

@api.route("/vend", methods=['POST'])
@ext_write_access
def vend():
	#print("vend(), request.values={}".format(request.values))
	channel = try_arg(request, 'channel', int)
	if channel not in server.items.channels():
		error("Channel does not exist")
	try:
		server.vend(channel)
	except ValueError:
		error("Insufficient credit", 402)
	except RuntimeError:
		error("Not ready to vend", 409) #HTTP Conflict
	return status(202)

@api.route("/channels/<int:channel>/vend", methods=['POST'])
@ext_write_access
def vend_fixed(channel):
	if channel not in server.items.channels():
		error("Channel does not exist", 404)
	try:
		server.vend(channel)
	except ValueError:
		error("Insufficient credit", 402)
	except RuntimeError:
		error("Not ready to vend", 409) #HTTP Conflict
	return status()

def default_arg(request, arg, typ=None, default=None):
	"""Try to find and coerce value in a Flask request,
	returning `default` if missing or invalid.

	`request`: `flask.Request` to search.    
	`arg`: Name of argument to search for.    
	`typ`: Type to coerce to (default `None`).    
	`default`: Default value to return on failure (default `None`).
	"""
	if arg not in request.values:
		return default
	if typ is None:
		return request.values[arg]
	try:
		return typ(request.values[arg])
	except ValueError:
		return default

def try_arg(request, arg, typ=None):
	"""Try to find and coerce value in a Flask request,
	   returning an API error if missing or invalid.

	`request`: `flask.Request` to search.    
	`arg`: Name of argument to search for.    
	`typ`: Type to coerce to (default `None`).
	"""
	if not request.values or arg not in request.values:
		error("Missing '{}' argument".format(arg))
	if typ is None:
		return request.values[arg]
	try:
		return typ(request.values[arg])
	except ValueError:
		error("Invalid '{}' argument".format(arg))

def error(msg="Invalid query", code=400):
	"""Make an API-friendly error.
	
	`msg`: Error message to return (default `"Invalid query"`).    
	`code`: HTTP status code to return (default `400`).
	"""
	json = {'error': msg}
	#return jsonify(json), code
	abort(make_response(jsonify(json), code))

@api.errorhandler(404)
def not_found(error):
	json = {'error': 'Not found'}
	return make_response(jsonify(json), 404)

@api.errorhandler(403)
def not_found(error):
	json = {'error': 'Forbidden'}
	return make_response(jsonify(json), 403)
