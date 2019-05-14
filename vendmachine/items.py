import os
import yaml

class Items():
	def __init__(self, itemPath="", itemFile="items.yaml", autosave=True):
		self.autosave = autosave
		if os.path.isabs(itemFile):
			self._itemFile = itemFile #file provided in configuration is already absolute
		else:
			self._itemFile = os.path.join(itemPath, itemFile) #combine with config directory
		self.load()

	def load(self):
		if os.path.isfile(self._itemFile):
			print("Loading item list")
			try:
				with open(self._itemFile, "r") as f:
					try:
						self._items = yaml.safe_load(f)
					except yaml.YAMLError as e:
						print("Invalid YAML File: '{}'".format(self._itemFile))
						print("details: {}".format(e))
						raise
			except EnvironmentError as e:
				print("Unable to open items file '{}'".format(self._itemFile))
				raise
		else:
			if os.path.exists(self._itemFile):
				raise EnvironmentError("Config path '{}' exists but is not a file".format(self._itemFile))
			print("Creating item list")
			self._items = {}
			self.dirty()

	def add(self, channel, price, motor, name=None, qty=0):
		if channel in self._items:
			raise ValueError("Item already exists")
		self._items[channel] = {
			"price": float(price),
			"name": str(name),
			"qty": int(qty),
			"motor": int(motor),
		}
		self.dirty()

	def update(self, channel, price=None, motor=None, name=None, qty=None):
		if channel not in self._items:
			raise ValueError("Item does not exist")
		item = self._items[channel]
		dirty = False
		if price != None:
			item["price"] = price
			dirty = True
		if motor != None:
			item["motor"] = motor
			dirty = True
		if name != None:
			item["name"] = name
			dirty = True
		if qty != None:
			item["qty"] = qty
			dirty = True
		if dirty:
			self.dirty()
		else:
			raise ValueError("No entries changed")
	
	def dirty(self):
		self._dirty = True
		if self.autosave:
			self.save()
	
	def is_dirty(self):
		return self._dirty

	def items(self):
		return self._items

	def __len__(self):
		return len(_items)

	def __getitem__(self, item):
		return self._items[item]

	def __contains__(self, item):
		return item in self._items

	def exit(self):
		if self._dirty:
			try:
				self.save()
			except EnvironmentError: #can't do much, just shutdown anyway.
				pass

	def save(self, itemFile=None):
		if itemFile == None:
			itemFile = self._itemFile
			print("Saving item list")
		else:
			if os.path.exists(itemFile) and not os.path.isfile(itemFile):
				raise EnvironmentError("Config path '{}' exists but is not a file".format(itemFile))
			print("Saving item list to file '{}'".format(itemFile))
		try:
			with open(itemFile, "w") as f:
				yaml.safe_dump(self._items, f)
			self._dirty = False
		except EnvironmentError as e:
			print("Unable to save item list.\nError: {}".format(e))
			raise
