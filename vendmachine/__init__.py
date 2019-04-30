#!/usr/bin/env python3

from vendmachine.server import server
import vendmachine.settings

def main():
	s = settings.init()
	server.setup()
	server.run()
	from vendmachine.server import socketio, app
	socketio.run(app, debug=True, host=s.get(["server", "host"]), port=s.get(["server", "port"]))

if __name__ == "__main__":
	main()
