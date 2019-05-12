"""Initialize and run the server.

This function also sets up handlers to respond to system shutdown signals.
"""

import sys
import signal

from vendmachine.server import server

def main():
	def kill(signum=None, frame=None):
		"""Gracefully shut down the server and GPIO interface.
		:param signum: The number of the system signal received. Currently unused.
		:param frame: The current stack frame. Currently unused.

		"""
		print("Shutting down...")
		server.stop()
		sys.exit(0)

	signal.signal(signal.SIGINT, kill) #^C or similar
	signal.signal(signal.SIGTERM, kill) #kill, etc.

	import vendmachine.settings
	server.setup()
	server.run()

if __name__ == '__main__':
	main()
