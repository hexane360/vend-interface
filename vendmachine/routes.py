#!/usr/bin/env python3

from flask import render_template, abort

from vendmachine.server import app, socketio
from vendmachine.settings import settings

@socketio.on('connect')
def connect():
	print("Connected")

def messageReceived(methods=['GET', 'POST']):
	print('message was received!!!')

@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
	print('received my event: ' + str(json))
	socketio.emit('my response', json, callback=messageReceived)

@app.route("/")
def root():
    return render_template("main.html")

@app.route("/base")
def template():
	print("base.html")
	return render_template("base.html")
