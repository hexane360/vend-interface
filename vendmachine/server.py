#!/usr/bin/env python3

from enum import IntEnum, unique

from flask import Flask
from flask_socketio import SocketIO

from vendmachine.machine import *

app = Flask("vendmachine") #instance_relative_config=True
socketio = SocketIO(app)

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

	def setup(self):
		from vendmachine.settings import settings as s
		secret_key = s.get(["server", "secretKey"])
		if not secret_key:
			print("Generating server key")
			import string
			from random import choice
			chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
			secret_key = "".join(choice(chars) for _ in range(32))
			s.set(["server", "secretKey"], secret_key)
			s.save()

	def status_data(self):
		return {'status': {
					"code": self._status.value,
					"text": str(self._status),
					"credit": self._credit,
					"creditText": "${:,.2f}".format(self._credit) } }

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
		socketio.emit('status', self.status_data())

	def vend(self, item):
		if self._credit < item["price"]:
			raise ValueError("Insufficient Credit")
		self._credit -= item["price"]
		self.status_change(Status.Vending)
		try:
			self.machine.vend(item["motor"])
		except Exception as e:
			print("Vending error: ".format(e))
			self._credit += item["price"]
		self.status_change(Status.Ready)

	def run(self):
		self.machine = Machine()
		self.machine.oosEvent(oosEvent) #register interrupt
		self.machine.activateInterrupts()
		global app, socketio
		import vendmachine.routes
		from vendmachine.api import api
		app.register_blueprint(api, url_prefix="/api") #subdomain="api"
		#print("server.run()")

server = Server()
