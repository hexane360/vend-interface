#!/usr/bin/env python3

import os
import yaml

settings = None #held globally so it can be accessed outside a Server

default_settings = {
	"server": {
		"host": "127.0.0.1",
		"port": 5000
	},
	"appearance": {
	},
	"logging": {
		"log_file": "/home/vend/server_log",
		"log_level": 4
	},
	"files": {
		"items": "items.yaml",
		"users": "users.yaml",
	}
}

class Settings():
	def __init__(self, configFile=None):
		if configFile is not None:
			self._configfile = configFile
		else:
			self._configfile = os.path.join("", "config.yaml")

		self._settings = default_settings #not a deep copy - be careful
		if os.path.exists(self._configfile) and os.path.isfile(self._configfile):
			print("Loading config")
			with open(self._configfile, "r") as f:
				try:
					new_settings = yaml.safe_load(f)
					#self._mtime = self.last_modified
				except yaml.YAMLError as e:
					print("Invalid YAML File: {}".format(self._configfile))
					print("details: {}".format(e))
					raise
				self._settings.update(new_settings)
		else:
			print("Writing default setings")
			with open(self._configfile, "w") as f:
				yaml.safe_dump(default_settings, f)
	def get(self, keys):
		try:
			if hasattr(keys, "index") and not hasattr(keys, "split"):
				node = self._settings
				for key in keys:
					node = node[key]
				return node
			else: #treat as scalar
				return self._settings[keys]
		except:
			return None
	def set(self, keys, val):
		if hasattr(keys, "index") and not hasattr(keys, "split"):
			if len(keys) == 0:
				raise ValueError("Empty key list")
			node = self._settings
			for key in keys[:-1]:
				if key not in node:
					node[key] = {}
				node = node[key]
			node[keys[-1]] = val
		else: #treat as scalar
			self._settings[keys] = val
	def save(self):
		print("Saving configuration")
		with open(self._configfile, "w") as f:
			yaml.safe_dump(self._settings, f)

def init(configFile=None):
	global settings
	if settings is None: #only create one Settings
		settings = Settings(configFile)
	return settings
