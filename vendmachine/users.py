import os
import yaml

import hashlib
import secrets

#this is a mess

global apiuser

class Users():
	def __init__(self, usersFile="users.yaml"):
		self.autosave = True
		self._dirty = False
		self._usersFile = usersFile
		self.load(usersFile)

	def load(self, usersFile=None):
		if usersFile == None:
			usersFile = self._usersFile
		if os.path.exists(usersFile) and os.path.isfile(usersFile):
			print("Loading user list")
			with open(usersFile, "r") as f:
				try:
					users = yaml.safe_load(f)
				except yaml.YAMLError as e:
					print("Invalid YAML File: {}".format(usersFile))
					print("details: {}".format(e))
					raise
				for obj in users:
					uid = obj.get("id") or self._gen_uid()
					user = User(uid, obj)
					if uid in self._users:
						raise ValueError("UID {} already in use".format(uid))
					self._users[uid] = user
				self.dirty(None)
		else:
			print("Creating user list")
			self._users = {}
			with open(usersFile, "w") as f:
				yaml.safe_dump([], f)
			self.dirty()
	
	def _gen_uid(self):
		 return 5
	
	def add(self, obj, uid=None):
		if uid is None:
			uid = self._gen_uid()
		if uid in self._users:
			raise ValueError("UID {} already in use".format(uid))
		self._users[uid] = User(uid, obj)
		self.dirty()
	
	def find(self, uid=None, name=None, apikey=None, admin=None, active=None):
		if uid is not None:
			item = self._items.get(uid)
			if item.matches(uid=uid, name=name, apikey=apikey, admin=admin, active=active):
				return [item]
			else:
				return []
		matches = []
		for item in self._items:
			if item.matches(uid=uid, name=name, apikey=apikey, admin=admin, active=active):
				matches.append(item)
		return matches
	
	def find_one(self, uid=None, name=None, apikey=None, admin=None, active=None):
		matches = self.find(uid=uid, name=name, apikey=apikey, admin=admin, active=active)
		if len(matches) == 0:
			return None
		if len(matches) > 1:
			print("Warning: More than one user match search criteria (probably apikey)")
		return matches[0]
	
	def __del__(self, uid):
		del self._users[uid]
		self._dirty = True
		
	def dirty(self, dirty=True):
		if dirty is None: #check to see if dirty
			if not self.is_dirty():
				return
		self._dirty = True
		if self.autosave:
			self.save()

	def is_dirty(self):
		if self._dirty:
			return True
		for user in self._users:
			if user.is_dirty():
				return True
		return False

	def __len__(self):
		return len(_users)

	def __getitem__(self, uid):
		return self._users[uid]

	def __contains__(self, uid):
		return uid in self._users
	
	def exit(self):
		if self.is_dirty():
			self.save()

	def save(self, usersFile=None):
		print("Saving item list")
		if usersFile == None:
			usersFile = self._usersFile
		with open(usersFile, "w") as f:
			yaml.safe_dump([user.to_dict() for user in self._users.values()], f)
		self._dirty = False
		for user in self._users:
			user._dirty = False

class User():
	def __init__(self, uid, obj):
		self._dirty = False
		self._id = uid
		if "name" not in obj:
			raise KeyError("User {} has no 'name' attribute".format(uid))
		self._active = bool(obj["active"]) if "active" in obj else True
		self._admin = bool(obj["admin"]) if "admin" in obj else False
		self._apikey = obj.get("apikey")
		if "password" not in obj:
			print("No password for user `{}`. Disabling".format(name))
			self._has_password = False
		else:
			if "salt" not in obj:
				#hash password
				self._salt = secrets.token_urlsafe(32)
				hasher = hashlib.sha512()
				hasher.update(obj["password"])
				hasher.update(self._salt)
				self._password = hasher.hexdigest()
				self._dirty = True
			else:
				self._salt = obj["salt"]
				self._password = obj["password"]
	def to_dict(self):
		obj = { "name": self._name,
		        "id": self._id,
		        "admin": self._admin,
		        "active": self._active }
		if self._has_password:
			obj["password"] = self._password
			obj["salt"] = self._salt
		if self._apikey is not None:
			obj["apikey"] = self._apikey
		return obj
	def matches(self, name=None, admin=None, active=None, apikey=None):
		if apikey is not None and self._apikey != apikey:
			return False
		if name is not None and self._name != name:
			return False
		if admin is not None and self._admin != admin:
			return False
		if active is not None and self._active != active:
			return False
		return True
	def is_dirty(self):
		return self._dirty
	def apikey(self):
		return self._apikey
	def __eq__(self, other):
		return self._id == other._id
	#methods required by flask_login:
	def get_id(self):
		return self._id
	def is_authenticated(self):
		return True
	def is_active(self):
		return self._active and self._has_password
	def is_anonymous(self):
		return False

class Anon():
	def __init__(self, uid=1):
		self._id = uid
	def get_id(self):
		return self._id
	def is_authenticated(self):
		return False
	def is_active(self):
		return True
	def is_anonymous(self):
		return True

class ApiUser():
	def __init__(self, uid=0):
		self._id = uid
	def get_id(self):
		return self._id
	def is_authenticated(self):
		return True
	def is_active(self):
		return True
	def is_anonymous(self):
		return True

apiuser = ApiUser()
