#!/usr/bin/env python3

import secrets
from enum import IntEnum, unique

from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager

from vendmachine.items import Items
from vendmachine.machine import Machine

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
		self.settings = None
		self._status = Status.Ready
		self._credit = 0.0
		self.items = Items()
		self.app = None
		self.host = None
		self.port = None
		self.socketio = None
		self.logins = None
		self.machine = None

	def setup(self):
		from vendmachine.settings import init
		self.settings = init()
		secret_key = self.settings.get(["server", "secretKey"])
		if not secret_key:
			print("Generating server key")
			secret_key = secrets.token_urlsafe(32)
			self.settings.set(["server", "secretKey"], secret_key)
			self.settings.save()
		self.app = Flask("vendmachine")
		self.app.secret_key = secret_key
		self.port = self.settings.get(["server", "port"])
		self.host = self.settings.get(["server", "host"])
		self.socketio = SocketIO(self.app)

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
	def add_credit(self, credit):
		self._credit += credit
		self.status_update()
	def pulse_event(self):
		print("Recording pulse")
		self.add_credit(1.0)

	def oos_event(self, value):
		if not value:
			print("Bill acceptor out of service")
		else:
			print("Bill acceptor back in service")

	def status_update(self):
		print("status, credit={}".format(self._credit))
		self.socketio.emit('status', self.status_data())

	def error(self, msg="Unknown error", code=0):
		json = {"error": {
			"code": code,
			"msg": msg,
		}}
		self.socketio.emit('error', json)

	def vend(self, item):
		if self._credit < item["price"]:
			raise ValueError("Insufficient Credit")
		self._credit -= item["price"]
		self.status_change(Status.Vending)
		try:
			self.machine.vend(item["motor"])
		except Exception as e:
			print("Vending error: {}".format(e))
			self._credit += item["price"]
			self.error(str(e), 1)
		self.status_change(Status.Ready)

	def run(self):
		self.machine = Machine()
		self.machine.oosEvent(self.oos_event) #register interrupts
		self.machine.pulseEvent(self.pulse_event)
		import vendmachine.routes
		from vendmachine.api import api
		from vendmachine.ext import ext
		self.app.register_blueprint(api, url_prefix="/api") #subdomain="api"
		self.app.register_blueprint(ext, url_prefix="/ext")
		self.app.register_blueprint(api, url_prefix="/ext/api")
		self.socketio.run(self.app, debug=True, use_reloader=False, host=self.host, port=self.port)

	def stop(self):
		if self.logins is not None:
			print("Saving logins")
			self.logins.save()
		if self.items is not None:
			print("Saving items")
			self.items.save()
		if self.settings is not None:
			print("Saving settings")
			self.settings.save()
		if self.machine is not None:
			print("Closing GPIO")
			self.machine.stop()
		if self.socketio is not None:
			print("Sending socket shutdown")
			self.socketio.emit('shutdown')
		#other things to do?

server = Server()
