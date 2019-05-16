#!/usr/bin/env python3

import os
import yaml
import collections

config = None #held globally so it can be accessed outside a Server

default_config = {
	"server": {
		"host": "127.0.0.1",
		"port": 5000
	},
	"access": {
		"restrict_read": True,
		"restrict_write": True,
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
		"autosave": True,
	}
}

def recursive_update(old, new):
	for k, v in new.items():
		if isinstance(v, collections.Mapping):
			old[k] = recursive_update(old.get(k, {}), v)
		else:
			old[k] = v
	return old

class Config():
	def __init__(self, config_dir=""):
		self._config_file = os.path.join(config_dir, "config.yaml")

		self._config = default_config #not a deep copy - be careful
		if os.path.exists(self._config_file) and os.path.isfile(self._config_file):
			print("Loading config")
			with open(self._config_file, "r") as f:
				try:
					new_config = yaml.safe_load(f)
					#self._mtime = self.last_modified
				except yaml.YAMLError as e:
					print("Invalid YAML File: {}".format(self._config_file))
					print("details: {}".format(e))
					raise
				recursive_update(self._config, new_config)
				#self._config.update(new_config)
		else:
			print("Writing default setings")
			with open(self._config_file, "w") as f:
				yaml.safe_dump(default_config, f)
	def get(self, keys):
		try:
			if hasattr(keys, "index") and not hasattr(keys, "split"):
				node = self._config
				for key in keys:
					node = node[key]
				return node
			else: #treat as scalar
				return self._config[keys]
		except:
			return None
	def set(self, keys, val):
		if hasattr(keys, "index") and not hasattr(keys, "split"):
			if len(keys) == 0:
				raise ValueError("Empty key list")
			node = self._config
			for key in keys[:-1]:
				if key not in node:
					node[key] = {}
				node = node[key]
			node[keys[-1]] = val
		else: #treat as scalar
			self._config[keys] = val
	def save(self):
		print("Saving configuration")
		with open(self._config_file, "w") as f:
			yaml.safe_dump(self._config, f)

def init(config_dir=None):
	global config
	if config is None: #only create one Settings
		config = Config(config_dir)
	return config
