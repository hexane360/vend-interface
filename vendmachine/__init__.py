#!/usr/bin/env python3

import signal
import sys

from vendmachine.server import server
import vendmachine.settings

def kill(signum, frame):
	print("Shutting down...")
	server.stop()
	sys.exit(0)

def main():
	signal.signal(signal.SIGINT, kill) #^C or similar
	signal.signal(signal.SIGTERM, kill) #kill, etc.
	server.setup()
	server.run()

if __name__ == "__main__":
	main()
