#!/usr/bin/env python3

"""Handles the actual starting and stopping of the server.

The only reason this file exists is to provide a public
place to document what happens in `vendmachine/__main__.py`.
"""

import sys
import signal

from vendmachine.server import init_server

def kill(signum=None, frame=None):
	"""Gracefully shut down the server and GPIO interface.
 
	`signum` is the code of the system signal received. Currently unused.    
	`frame` is the current stack frame. Currently unused.
	"""
	print("Shutting down...")
	server.stop()
	sys.exit(0)

def main():
	"""Initialize and run the server.

	This function also sets up handlers to respond to system shutdown signals.
	"""
	signal.signal(signal.SIGINT, kill) #^C or similar
	signal.signal(signal.SIGTERM, kill) #kill, etc.

	global server #allows kill to access server.stop()
	server = init_server()
	server.setup()
	server.run()
