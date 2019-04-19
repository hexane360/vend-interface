#!/usr/bin/env python3

from vendmachine.server import Server
from vendmachine.settings import Settings

def main():
	server = Server() #initalize the server object (in server.py)
	server.run()
	from vendmachine.server import app
	app.run() #start the flask app

if __name__ == "__main__":
	main()
