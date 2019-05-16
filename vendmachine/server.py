#!/usr/bin/env python3

"""Holds and manages the main state of the program.

Includes `Server` class as well as a `Status` enum describing the current
state of the machine. 

Get a global `Server` object using `init_server()`.

"""

#handle a few common mistakes
try:
	import secrets
except ImportError:
	raise ImportError("Module requires Python >3.6")
try:
	from flask import Flask
	from flask_login import LoginManager
except ImportError:
	raise ImportError("Unable to find Flask. Module must be run from up-to-date virtualenv.")

from enum import IntEnum, unique
import time
import eventlet

from vendmachine.items import Items
from vendmachine.users import Users

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

server = None
"""Global `Server` instance to be shared by all modules.

.. warning:: This will be `None` until `init_server()` is first called.
"""

class Server():

	"""The class holding everything together.
	
	Most items are uninitalized before calling `Server.setup()`,
	which also accepts a configuration directory.
	
	`Server.run()` actually starts the SocketIO/Flask server,
	and `Server.stop()` should be called to gracefully shutdown.

	"""

	def __init__(self):
		self._status = Status.Ready
		self._credit = 0.0
		self.config = None
		"""`vendmachine.config.Config` object containing all server settings."""
		self.items = None
		"""`vendmachine.items.Items` object managing vending machine inventory."""
		self.users = None
		"""`vendmachine.users.Users` object managing all authorized users."""
		self.app = None
		"""`flask.Flask` object containing the main Flask application."""
		self.socketio = None
		"""`flask_socketio.SocketIO` object containing the main socketio server.
		
		Ultimately responsible for actually running the Flask app."""
		self.login_manager = LoginManager()
		"""`flask_login.LoginManager` handling user sessions and authentication."""
		self._host = None
		self._port = None
		self.machine = None

	def setup(self, config_dir=""):
		"""Setup the Server's configurations, outputs, and Flask objects.
		
		If `config_dir` is specified, look there for `config.yaml`. Otherwise
		look in the current directory.
		
		Also handles generating or loading a secret key for the Flask server.
		
		After this function, the following properties should be initalized (not `None`):

		- `Server.config` as `vendmachine.config.Config`
		- `Server.items` as `vendmachine.items.Items`
		- `Server.users` as `vendmachine.users.Users`
		- `Server.app` as `flask.Flask`
		- `Server.socketio` as `flask_socketio.SocketIO`
		- `Server.login_manager` as `flask_login.LoginManager`
		
		"""
		from vendmachine.config import init
		self.config = init(config_dir)
		print("Autosave {}".format("enabled" if self.config.get(["files", "autosave"]) else "disabled"))
		self.items = Items(config_dir, self.config.get(["files", "items"]), self.config.get(["files", "autosave"]))
		self.users = Users(config_dir, self.config.get(["files", "users"]), self.config.get(["files", "autosave"]))

		secret_key = self.config.get(["server", "secretKey"])
		if not secret_key:
			print("Generating server key")
			secret_key = secrets.token_urlsafe(32)
			self.config.set(["server", "secretKey"], secret_key)
			self.config.save()
		self.app = Flask("vendmachine")
		self.app.secret_key = secret_key

		#from vendmachine.users import Users
		#self.logins = Users(config_dir, self.config.get(["files", "users"]))

		self.login_manager.init_app(self.app)

		self._port = self.config.get(["server", "port"])
		self._host = self.config.get(["server", "host"])

		from flask_socketio import SocketIO
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
		print("status {}, credit={}".format(str(self._status), self._credit))
		self.socketio.emit('status', self.status_data())		

	def vend(self, channel):
		if channel not in self.items.channels():
			raise KeyError("Channel not active")
		motor = self.items.get_channel(channel)["motor"]
		price = self.items.get_item(channel=channel)["price"]
		if self._status != Status.Ready:
			raise RuntimeError("Not ready to vend")
		if self._credit < price:
			raise ValueError("Insufficient Credit")
		self._credit -= price
		self.status_change(Status.Vending)
		eventlet.spawn(self._vendTask, motor, price) #allows websocket to continue

	def _vendTask(self, motor, price):
		try:
			if self.machine is not None:
				self.machine.vend(motor)
			else:
				print("Simulating vend on motor {}".format(motor))
				eventlet.sleep(5)
				#raise ValueError("Example Error")
				print("Simulated vend done")
			self.socketio.emit('vendSuccess', {})
		except Exception as e:
			print("Vending error: {}".format(e))
			self._credit += price
			json = {"error": {
				"code": 1,
				"msg": str(e),
			}}
			self.socketio.emit('vendError', json)
		self.status_change(Status.Ready)

	def run(self):
		try:
			from RPi import GPIO
			from vendmachine.machine import Machine
			self.machine = Machine()
			self.machine.oosEvent(self.oos_event) #register interrupts
			self.machine.pulseEvent(self.pulse_event)
		except (ModuleNotFoundError, RuntimeError):
			print("Running simulated Machine")
			self.machine = None
		import vendmachine.routes
		from vendmachine.api import api
		from vendmachine.ext import ext
		self.app.register_blueprint(api, url_prefix="/api") #subdomain="api"
		self.app.register_blueprint(ext, url_prefix="/ext")
		self.app.register_blueprint(api, url_prefix="/ext/api") #, auth=True
		self.socketio.run(self.app, debug=True, use_reloader=False, host=self._host, port=self._port)

	def stop(self):
		if self.users is not None:
			self.users.exit()
		if self.items is not None:
			self.items.exit()
		if self.config is not None:
			#print("Saving config")
			self.config.save()
		if self.machine is not None:
			#print("Closing GPIO")
			self.machine.stop()
		if self.socketio is not None:
			print("Sending socket shutdown")
			self.socketio.emit('shutdown')
		#other things to do?

def init_server():
	global server
	if server is None:
		server = Server()
	return server
