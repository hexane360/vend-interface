#!/usr/bin/env python3

from vendmachine.server import server
import vendmachine.settings

def main():
	s = settings.init()
	server.setup()
	server.run()

if __name__ == "__main__":
	main()
