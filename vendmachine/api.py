#!/usr/bin/env python3

from flask import Blueprint, request, jsonify, abort, make_response
import json

from vendmachine.server import server, app, socketio, Status
from vendmachine.settings import settings
from vendmachine.items import Items
items = Items()

api = Blueprint("api", __name__)

@api.route("/status", methods=['GET'])
def status():
	return jsonify(server.status_data()), 200

@api.route("/refresh", methods=['POST'])
def refresh():
	socketio.emit('refresh')
	return status()

@api.route("/credit", methods=['POST'])
def credit():
	if not request.values or "amount" not in request.values:
		error("Missing 'amount' argument")
	try:
		amount = float(request.values["amount"])
	except ValueError:
		error("Invalid 'amount' argument")
	server.set_credit(amount)
	return status()

@api.route("/items", methods=['GET'])
def get_items():
	return jsonify({"items": items.items()})

@api.route("/item/<int:addr>", methods=['PUT'])
def update_item(addr):
	if not request.values:
		error("Missing arguments")
	price = default_arg(request, 'price', float)
	name = default_arg(request, 'name', str)
	qty = default_arg(request, 'qty', int)
	try:
		items.update(addr, price, name, qty)
	except ValueError:
		error("Invalid item properties")
	return jsonify({"item": items[addr]}), 200

@api.route("/item/<int:addr>", methods=['GET'])
def get_item(addr):
	if addr not in items:
		error("Item does not exist", 404)
	return jsonify({"item": items[addr]}), 200

@api.route("/price", methods=['GET'])
def price():
	print("price: {}".format(request.values['addr']))
	addr = try_arg(request, 'addr', int)
	if addr not in items:
		error("Item does not exist")
	price = items[addr]['price']
	return jsonify({"price": price, "text": "${:,.2f}".format(price)})
	

@api.route("/item/<int:addr>/price", methods=['GET'])
def price_fixed(addr):
	if addr not in items:
		error("Item does not exist", 404)
	price = items[addr]['price']
	return jsonify({"price": price, "text": "${:,.2f}".format(price)})

@api.route("/vend", methods=['POST'])
def vend():
	#print("vend(), request.values={}".format(request.values))
	addr = try_arg(request, 'addr', int)
	if addr not in items:
		error("Item does not exist")
	try:
		server.vend(items[addr])
	except ValueError:
		error("Insufficient credit", 402)
	return status()

@api.route("/item/<int:addr>/vend", methods=['POST'])
def vend_fixed(addr):
	if addr not in items:
		error("Item does not exist", 404)
	try:
		server.vend(items[addr])
	except ValueError:
		error("Insufficient credit", 402)
	return status()

def default_arg(request, arg, typ=int, default=None):
	if arg not in request.values:
		return default
	try:
		return typ(request.values[arg])
	except ValueError:
		return default

def try_arg(request, arg, typ=int):
	if not request.values or arg not in request.values:
		error("Missing '{}' argument".format(arg))
	try:
		return typ(request.values[arg])
	except ValueError:
		error("Invalid '{}' argument".format(arg))

def error(msg="Invalid query", code=400):
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
	return make_response(jsonify(json), 404)
