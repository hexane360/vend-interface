#!/usr/bin/env python3

from flask import Blueprint, request, abort
import json

from vendmachine.server import app
from vendmachine.settings import settings

api = Blueprint("api", __name__)

items = {99: {
				 "price": 2.0,
				 "name": "Item A",
				 "qty": 5
	         },
         98: {
				 "price": 3.0,
				 "name": "Item B",
				 "qty": 2
	         }
         }

#get method
@api.route("/price", methods=['GET'])
def check_price():
	if not request.args or 'address' not in request.args:
		abort(400)
	try:
		address = int(request.args['address'])
	except ValueError:
		abort(400)
	#print(request.form['data'])
	if items[address] is None:
		abort(400) #bad request
	return "${.2}".format(items[address]["price"])

@api.route("/status", methods=['GET'])
def status():
	return status

@api.route("/vend/<channel>", methods=['POST'])
def vend(channel):
	try:
		channel = int(channel)
	except ValueError:
		abort(400) #bad request
	if userDollars < item["price"]:
		abort(400)
	#vend item
	userDollars -= item["price"]

@api.route("/item", methods=['POST'])
def post_item():
	if not request.args or 'address' not in request.args or 'price' not in request.args:
		abort(400)
	try:
		address = int(request.args['address'])
		price = float(request.args['price'])
	except ValueError:
		abort(400)
	qty = request.args['qty'] or 0
	name = request.args['name'] or ""
	items['address'] = {
		"price": price,
		"name": name,
		"qty": qty
	}
	return 200

@api.route("/item", methods=['GET'])
def get_item():
	if not request.args or 'address' not in request.args:
		abort(400)
	try:
		address = int(request.args['address'])
	except ValueError:
		abort(400)
	return json.dumps(items[address])
