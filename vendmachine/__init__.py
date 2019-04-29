#!/usr/bin/env python3

from vendmachine.server import Server
import vendmachine.settings

def main():
	settings.init()
	server = Server() #initalize the server object (in server.py)
	server.run()
	from vendmachine.server import socketio, app
	socketio.run(app, debug=True)

if __name__ == "__main__":
	main()
