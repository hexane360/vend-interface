#!/usr/bin/env python3

settings = None

class Settings():
	def __init__(self, configFile):
		pass

def init(configFile=None):
	global settings
	settings = Settings(configFile)
