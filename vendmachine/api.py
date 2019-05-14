#!/usr/bin/env python3

"""Main API for all clients.

"""

from flask import Blueprint, request, jsonify, abort, make_response
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

@api.route("/status", methods=['GET'])
@ext_read_access
def status():
	"""Return the machine status, as defined in `Server.status_data()`.
	
	Requires user access.
	"""
	return jsonify(server.status_data()), 200

@api.route("/refresh", methods=['POST'])
@ext_admin_access
def refresh():
	"""Ask all websocket clients to refresh themselves."""
	socketio.emit('refresh')
	return status()

@api.route("/credit", methods=['POST'])
@ext_write_access
def set_credit():
	if not request.values or "amount" not in request.values:
		error("Missing 'amount' argument")
	try:
		amount = float(request.values["amount"])
	except ValueError:
		error("Invalid 'amount' argument")
	server.set_credit(amount)
	return status()

@api.route("/credit", methods=['GET'])
@ext_read_access
def get_credit():
	return jsonify({"credit": server.credit()}), 200

@api.route("/items", methods=['GET'])
@ext_read_access
def get_items():
	return jsonify({"items": server.items.items()})

@api.route("/item/<int:addr>", methods=['PUT'])
@ext_write_access
def update_item(addr):
	if not request.values:
		error("Missing arguments")
	price = default_arg(request, 'price', float)
	name = default_arg(request, 'name', str)
	qty = default_arg(request, 'qty', int)
	try:
		server.items.update(addr, price, name, qty)
	except ValueError:
		error("Invalid item properties")
	return jsonify({"item": server.items[addr]}), 200

@api.route("/item/<int:addr>", methods=['GET'])
@ext_read_access
def get_item(addr):
	if addr not in server.items:
		error("Item does not exist", 404)
	return jsonify({"item": server.items[addr]}), 200

@api.route("/price", methods=['GET'])
@ext_read_access
def price():
	print("price: {}".format(request.values['addr']))
	addr = try_arg(request, 'addr', int)
	if addr not in server.items:
		error("Item does not exist")
	price = server.items[addr]['price']
	return jsonify({"price": price, "text": "${:,.2f}".format(price)})
	

@api.route("/item/<int:addr>/price", methods=['GET'])
@ext_read_access
def price_fixed(addr):
	if addr not in server.items:
		error("Item does not exist", 404)
	price = server.items[addr]['price']
	return jsonify({"price": price, "text": "${:,.2f}".format(price)})

@api.route("/vend", methods=['POST'])
@ext_write_access
def vend():
	#print("vend(), request.values={}".format(request.values))
	addr = try_arg(request, 'addr', int)
	if addr not in server.items:
		error("Item does not exist")
	try:
		server.vend(server.items[addr])
	except ValueError:
		error("Insufficient credit", 402)
	return status()

@api.route("/item/<int:addr>/vend", methods=['POST'])
@ext_write_access
def vend_fixed(addr):
	if addr not in server.items:
		error("Item does not exist", 404)
	try:
		server.vend(server.items[addr])
	except ValueError:
		error("Insufficient credit", 402)
	return status()

def default_arg(request, arg, typ=int, default=None):
	"""Try to find and coerce value in a Flask request,
	returning 'default' if missing or invalid.

	`request`: `flask.Request` to search.    
	`arg`: Name of argument to search for.    
	`typ`: Type to coerce to (default `int`).    
	`default`: Default value to return on failure (default `None`).
	"""
	if arg not in request.values:
		return default
	try:
		return typ(request.values[arg])
	except ValueError:
		return default

def try_arg(request, arg, typ=int):
	"""Try to find and coerce value in a Flask request,
	   throwing ValueError if missing or invalid.

	`request`: `flask.Request` to search.    
	`arg`: Name of argument to search for.    
	`typ`: Type to coerce to (default `int`).
	"""
	if not request.values or arg not in request.values:
		error("Missing '{}' argument".format(arg))
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
