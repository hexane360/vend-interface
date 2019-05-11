#!/usr/bin/env python3

"""
Flask server to provide a simple interface to the Mines Maker society's custom vending machine.
Requires Python 3.6 or newer.

Command-line options
====================
Currently, no command line options are accepted.

Configuration
=============
The behavior of the server can be configured using three YAML files:
 * config.yaml: Controls server settings (bind address, port, etc.). Further documented in settings.py
 * items.yaml: Controls inventory manifest for the vending machine. Further documented in items.py
 * users.yaml: Controls users and user permissions. Further documented in users.py
"""

import signal
import sys

from vendmachine.server import server
import vendmachine.settings

def kill(signum=None, frame=None):
	"""Gracefully shut down the server and GPIO interface.
	:param signum: The number of the system signal received. Currently unused.
	:param frame: The current stack frame. Currently unused.

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
	server.setup()
	server.run()

if __name__ == "__main__":
	main()
