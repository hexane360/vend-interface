#!/usr/bin/env python3

import signal

from vendmachine.server import server
import vendmachine.settings

def kill(signum, frame):
	print("Shutting down...")
	server.stop()
	s.close()

def main():
        signal.signal(signal.SIGINT, kill) #^C or similar
        signal.signal(signal.SIGTERM, kill) #kill, etc.
	s = settings.init()
	server.setup()
	server.run()

if __name__ == "__main__":
	main()
