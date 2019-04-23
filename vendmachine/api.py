#!/usr/bin/env python3

from flask import Blueprint, request, abort

from vendmachine.server import app
from vendmachine.settings import settings

api = Blueprint("api", __name__)

vendingArray = [{"address": 101, "price": 2},
                {"address": 102, "price": 3}
                ]

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
	item = find_item(vendingArray, address)
	if item is None:
		abort(400) #bad request
	return "${}".format(item["price"])

#post method
@api.route("/vend", methods=['POST'])
def vend(userInput, userDollars):
    item = find_item(vendingArray, userInput)
    if item is None:
        abort(400) #bad request
    if userDollars >= item["price"]:
        userDollars = userDollars - item["price"]
    else:
        abort(400) #bad request

#helper function
def find_item(vendingArray, userInput):
	for item in vendingArray:
		if item["address"] == userInput:
			return item
	return None
