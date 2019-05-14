#!/usr/bin/env python3

from flask import render_template, abort

from vendmachine.server import server
from vendmachine.config import config

try:
	socketio = server.socketio
	app = server.app
except AttributeError: #need to make Server for pdoc to run
	from vendmachine.server import init_server
	server = init_server()
	server.setup()
	socketio = server.socketio
	app = server.app

@socketio.on('connect')
def connect():
	#can return False to reject connection
	print("Websocket connected")

def messageReceived(methods=['GET', 'POST']):
	print('message was received!!!')

@socketio.on('status')
def status(json, methods=['GET', 'POST']):
	server.status_update()

@socketio.on('heartbeat')
def heartbeat(json, methods=['GET', 'POST']):
	print('received heartbeat: ' + str(json))
	socketio.emit('heartbeat', json, callback=messageReceived)

@app.route("/")
def root():
    return render_template("main.html")

@app.route("/base")
def template():
	print("base.html")
	return render_template("base.html")
