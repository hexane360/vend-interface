import os
import yaml

import hashlib
import secrets

#this is a mess

global api_user
global anon_user

class Users():
	def __init__(self, usersPath="", usersFile="users.yaml", autosave=True):
		self.autosave = autosave
		self._dirty = False
		self._users = {}
		if os.path.isabs(usersFile):
			self._usersFile = usersFile #file provided in configuration is already absolute
		else:
			self._usersFile = os.path.join(usersPath, usersFile) #combine with config directory
		self.load()

	def load(self):
		if os.path.isfile(self._usersFile):
			print("Loading user list from file '{}'".format(self._usersFile))
			try:
				with open(self._usersFile, "r") as f:
					try:
						users = yaml.safe_load(f)
					except yaml.YAMLError as e:
						print("Invalid YAML File: '{}'".format(self._usersFile))
						print("details: {}".format(e))
						raise
					for obj in users:
						user = User(obj)
						uid = user.get_id()
						if uid in self._users:
							raise ValueError("Username {} already in use".format(uid))
						self._users[uid] = user
					self.dirty(None)
			except EnvironmentError as e:
				print("Unable to open users file '{}'".format(self._usersFile))
				raise
		else:
			if os.path.exists(self._usersFile):
				raise EnvironmentError("Config path '{}' exists but is not a file".format(self._usersFile))
			print("Creating user list")
			self._users = {}
			with open(self._usersFile, "w") as f:
				yaml.safe_dump([], f)
			self.dirty()
	
	#def _gen_uid(self):
		 #return 5
	
	def add(self, obj):
		#if uid is None
		#	uid = self._gen_uid()
		user = User(obj)
		uid = user.get_id()
		if uid in self._users:
			raise ValueError("UID {} already in use".format(uid))
		self._users[uid] = user
		self.dirty()
	
	def find(self, uid=None, name=None, apikey=None, admin=None, active=None):
		if uid is not None:
			user = self._users.get(uid)
			if user.matches(name=name, apikey=apikey, admin=admin, active=active):
				return [item]
			else:
				return []
		matches = []
		for user in self._users.values():
			if user.matches(name=name, apikey=apikey, admin=admin, active=active):
				matches.append(user)
		return matches
	
	def find_one(self, uid=None, name=None, apikey=None, admin=None, active=None):
		matches = self.find(uid=uid, name=name, apikey=apikey, admin=admin, active=active)
		if len(matches) == 0:
			return None
		if len(matches) > 1:
			print("Warning: More than one user match search criteria")
		return matches[0]
	
	def delete(self, uid):
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
		for user in self._users.values():
			if user.is_dirty():
				return True
		return False

	def __len__(self):
		return len(_users)

	def __getitem__(self, uid):
		return self._users[uid]
	
	def get(self, uid):
		return self._users.get(uid)

	def __contains__(self, uid):
		return uid in self._users
	
	def exit(self):
		if self.is_dirty():
			try:
				self.save()
			except EnvironmentError: #can't do much, just shutdown anyway.
				pass

	def save(self, usersFile=None):
		print("Saving user list")
		if usersFile == None:
			usersFile = self._usersFile
			print("Saving user list")
		else:
			if os.path.exists(usersFile) and not os.path.isfile(usersFile):
				raise EnvironmentError("Config path '{}' exists but is not a file".format(usersFile))
			print("Saving user list to file '{}'".format(usersFile))
		try:
			with open(usersFile, "w") as f:
				yaml.safe_dump([user.to_dict() for user in self._users.values()], f)
			self._dirty = False
			for user in self._users.values():
				user._dirty = False
		except EnvironmentError as e:
			print("Unable to save user list.\nError: {}".format(e))
			raise

class User():
	def __init__(self, obj):
		self._dirty = False
		if "name" not in obj:
			raise KeyError("User {} has no 'name' attribute".format(uid))
		self._id = obj["name"]
		self._active = bool(obj["active"]) if "active" in obj else True
		self.is_admin = bool(obj["admin"]) if "admin" in obj else False
		self._apikey = obj.get("apikey")
		if "password" not in obj:
			print("No password for user `{}`. Disabling".format(name))
			self._has_password = False
		else:
			if "salt" not in obj:
				#hash password
				self._salt = secrets.token_urlsafe(32)
				hasher = hashlib.sha512()
				hasher.update(obj["password"].encode())
				hasher.update(self._salt.encode())
				self._password = hasher.hexdigest()
				self._dirty = True
			else:
				self._salt = obj["salt"]
				self._password = obj["password"]
			self._has_password = True
		
		#properties required by flask_login
		self.is_authenticated = True
		self.is_active = self._active and self._has_password
		self.is_anonymous = False

	def check_pass(self, password):
		if not self._has_password:
			return False
		hasher = hashlib.sha512()
		hasher.update(password.encode())
		hasher.update(self._salt.encode())
		return hasher.hexdigest() == self._password

	def to_dict(self):
		obj = { "name": self._id,
		        "admin": self.is_admin,
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
		if admin is not None and self.is_admin != admin:
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
	#method required by flask_login:
	def get_id(self):
		return self._id

class AnonUser():
	def __init__(self):
		self.is_admin = False

		#properties required by flask_login
		self.is_authenticated = False
		self.is_active = True
		self.is_anonymous = True
	def get_id(self):
		return None

class ApiUser():
	def __init__(self):
		self.is_admin = True

		#properties required by flask_login
		self.is_authenticated = True
		self.is_active = True
		self.is_anonymous = False #not sure
	def get_id(self):
		return "API"

api_user = ApiUser()
anon_user = lambda: AnonUser() #factory to return new anonymous users
