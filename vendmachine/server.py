#!/usr/bin/env python3

from flask import Flask
from flask_socketio import SocketIO

app = Flask("vendmachine") #instance_relative_config=True
socketio = SocketIO(app)

class Server():
	def __init__(self):
		self._setup()

	def _setup(self): #not used yet
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

	def run(self):
		#init settings
		global app, socketio
		import vendmachine.routes
		from vendmachine.api import api
		app.register_blueprint(api, url_prefix="/api")
		#print("server.run()")
