#!/usr/bin/env python3

import secrets
from enum import IntEnum, unique

from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager

from vendmachine.items import Items
#from vendmachine.machine import *

def oosEvent(gpio, value):
	if not value: #out of service
		print("Bill acceptor out of service")
	else:
		print("Bill acceptor back in service")

@unique
class Status(IntEnum):
	Ready = 0
	Vending = 1
	NotReady = 2
	def __str__(self):
		return statusMap[self]
statusMap = {
	Status.Ready: "Ready",
	Status.Vending: "Vending",
	Status.NotReady: "Not ready"
}

global server

class Server():
	def __init__(self):
		self._status = Status.Ready
		self._credit = 0.0
		self.items = Items()
		self.app = None
		self.host = None
		self.port = None
		self.socketio = None
		self.logins = None

	def setup(self):
		from vendmachine.settings import settings as s
		secret_key = s.get(["server", "secretKey"])
		if not secret_key:
			print("Generating server key")
			secret_key = secrets.token_urlsafe(32)
			s.set(["server", "secretKey"], secret_key)
			s.save()

		self.app = Flask("vendmachine") #instance_relative_config=True
		self.app.secret_key = secret_key
		self.host = s.get(["server", "host"])
		self.port = s.get(["server", "port"])
		self.socketio = SocketIO(self.app)
		self.logins = LoginManager()
		self.logins.init_app(self.app)

	def status_data(self):
		return {"status": {
			"code": self._status.value,
			"text": str(self._status),
			"credit": self._credit,
			"creditText": "${:,.2f}".format(self._credit) }
		}

	def status(self):
		return self._status

	def status_change(self, status):
		self._status = status
		self.status_update()

	def credit(self):
		return self._credit

	def set_credit(self, credit):
		self._credit = credit
		self.status_update()

	def status_update(self):
		self.socketio.emit('status', self.status_data())

	def vend(self, item):
		if self._credit < item["price"]:
			raise ValueError("Insufficient Credit")
		self._credit -= item["price"]
		self.status_change(Status.Vending)
		try:
			#self.machine.vend(item["motor"])
			print("vend")
		except Exception as e:
			print("Vending error: ".format(e))
			self._credit += item["price"]
		self.status_change(Status.Ready)

	def run(self):
		#self.machine = Machine()
		#self.machine.oosEvent(oosEvent) #register interrupt
		#self.machine.activateInterrupts()
		import vendmachine.routes
		from vendmachine.api import api
		from vendmachine.ext import ext
		self.app.register_blueprint(api, url_prefix="/api") #subdomain="api"
		self.app.register_blueprint(ext, url_prefix="/ext")
		self.app.register_blueprint(api, url_prefix="/ext/api")
		self.socketio.run(self.app, debug=True, host=self.host, port=self.port)

server = Server()
