import os
import yaml

class Items():
	def __init__(self, itemPath="", itemFile="items.yaml", autosave=True):
		self.autosave = autosave
		self._defer = False
		if os.path.isabs(itemFile):
			self._itemFile = itemFile #file provided in configuration is already absolute
		else:
			self._itemFile = os.path.join(itemPath, itemFile) #combine with config directory
		self._used_motors = [None]*8 #stores which motor slots are currently used
		self.load()

	def load(self):
		if os.path.isfile(self._itemFile):
			print("Loading item list from file '{}'".format(self._itemFile))
			try:
				with open(self._itemFile, "r") as f:
					try:
						obj = yaml.safe_load(f)
					except yaml.YAMLError as e:
						print("Invalid YAML File: '{}'".format(self._itemFile))
						print("details: {}".format(e))
						raise
			except EnvironmentError as e:
				print("Unable to open items file '{}'".format(self._itemFile))
				raise
			self.defer(True)
			try:
				self._items = {}
				self._channels = {}
				if type(obj.get("items")) != dict:
					raise ValueError("Mapping 'items' missing from items file '{}'".format(self._itemFile))
				if type(obj.get("channels")) != dict:
					raise ValueError("Mapping 'channels' missing from items file '{}'".format(self._itemFile))
				items = obj["items"]
				channels = obj["channels"]
				for k, v in items.items():
					try:
						price = v["price"]
					except KeyError:
						print("Item '{}' missing price".format(k))
						raise
					self.add_item(k, **v)
				for k, v in channels.items():
					try:
						motor = v["motor"]
					except KeyError:
						print("Channel '{}' missing property 'motor'".format(k))
						raise
					qty = v.get("qty") #default qty to None (turned into 0)
					try:
						item = v["item"]
					except KeyError:
						print("Channel '{}' missing property 'item'".format(k))
						raise
					self.add_channel(k, item, motor, qty)
			except (KeyError, ValueError) as e:
				print("Error reading items file '{}'".format(self._itemFile))
				raise
			self.defer(False)
		else:
			if os.path.exists(self._itemFile):
				raise EnvironmentError("Config path '{}' exists but is not a file".format(self._itemFile))
			print("Creating item list")
			self._items = {}
			self.dirty()
	
	def add_item(self, name, price, **kwargs):
		if name in self._items:
			raise ValueError("Item '{}' already exists".format(name))
		self.replace_item(name, price, **kwargs)
	
	def replace_item(self, name, price, **kwargs):
		try:
			price = float(price)
		except ValueError:
			print("Invalid price '{}'".format(price))
		if price < 0:
			raise ValueError("Negative price '{}'".format(price))
		self._items[name] = kwargs
		self._items[name]["price"] = price
		self.dirty()

	def add_channel(self, channel, item, motor, qty=None):
		try:
			channel = int(channel)
		except ValueError:
			print("Invalid channel '{}'".format(channel))
		if channel in self._channels:
			raise ValueError("Item already exists in channel {}".format(channel))
		self.replace_channel(channel, item, motor, qty)
	
	def replace_channel(self, channel, item, motor, qty=None):
		try:
			channel = int(channel)
		except ValueError:
			print("Invalid channel '{}'".format(channel))
		if qty is None:
			qty = 0
		if channel < 0 or channel > 99:
			raise ValueError("Channel '{}' must be a two-digit number".format(channel))
		if item not in self._items:
			raise ValueError("Invalid item '{}'".format(item))
		try:
			motor = int(motor)
		except ValueError:
			print("Invalid motor '{}'".format(motor))
		if motor < 0 or motor > 7:
			raise ValueError("Channel '{}' has out-of-range motor '{}'".format(channel, motor))
		if self._used_motors[motor] is not None:
			raise ValueError("Motor '{}' is already in use by channel '{}'".format(motor, self._used_motors[motor]))
		self._used_motors[motor] = channel
		self._channels[channel] = {
			"item": str(item),
			"motor": motor,
			"qty": int(qty),
		}
		self.dirty()

	def update_channel(self, channel, motor=None, item=None, qty=None):
		if channel not in self._channels:
			raise ValueError("Channel '{}' does not exist".format(channel))
		channel = self._channels[channel]
		dirty = False
		if motor != None:
			try:
				motor = int(motor)
			except ValueError:
				print("Invalid motor '{}'".format(motor))
			if motor < 0 or motor > 7:
				raise ValueError("Out-of-range motor '{}'".format(motor))
			if self._used_motors[motor] is not None:
				raise ValueError("Motor '{}' is already in use my channel '{}'".format(motor, self._used_motors[motor]))
			self._used_motors[channel["motor"]] = None #old motor is no longer in use
			self._used_motors[motor] = channel #new motor is in use
			channel["motor"] = motor
			dirty = True
		if item != None:
			item = str(item)
			if item not in self._items:
				raise ValueError("Invalid item '{}'".format(item))
			channel["item"] = name
			dirty = True
		if qty != None:
			channel["qty"] = int(qty)
			dirty = True
		if dirty:
			self.dirty()
		else:
			raise ValueError("No entries changed")

	def update_item(self, name, price=None, **kwargs):
		if name not in self._items:
			raise ValueError("Item '{}' does not exist".format(name))
		item = self._items[name]
		dirty = False
		if price != None:
			try:
				price = float(price)
			except ValueError:
				print("Invalid price '{}'".format(price))
			if price < 0.0:
				raise ValueError("Negative price '{}".format(price))
			if item["price"] != price:
				dirty = True
			item["price"] = price
		for k, v in kwargs.items():
			if not dirty and (k not in item or item[k] != v):
				dirty = True
			item[k] = v
		if dirty:
			self.dirty()
		else:
			raise ValueError("No entries changed")
	
	def del_item(self, name):
		if name not in self._items:
			raise ValueError("Item '{}' does not exist".format(name))
		self.defer(True)
		del self._items[name]
		channels = []
		for channel, obj in self._channels.items():
			if obj["item"] == name:
				channels.append(channel)
		for channel in channels:
			self.del_channel(channel)
		self.dirty()
		self.defer(False)
		
	def del_channel(self, channel):
		if channel not in self._channels:
			raise ValueError("Channel '{}' does not exist".format(channel))
		self._used_motors[self._channels[channel]["motor"]] = None
		del self._channels[channel]
		self.dirty()

	def get_item(self, name=None, channel=None):
		if name is not None:
			return self._items.get(name)
		if channel is not None:
			if channel not in self._channels:
				return None
			return self._items[self._channels[channel]["item"]]
		raise ValueError("Must specify name or channel of item to search for")
	
	def get_channel(self, channel):
		return self._channels.get(channel) #should we return actual item along with this?
	
	def dirty(self):
		self._dirty = True
		if self.autosave and not self._defer:
			self.save()

	def defer(self, defer):
		self._defer = defer
		if not defer and self._dirty and self.autosave:
			self.save()
	
	def is_dirty(self):
		return self._dirty

	def items(self):
		return self._items
	
	def channels(self):
		return self._channels

	#def __len__(self):
	#	return len(self._items)
	#def __getitem__(self, item): #use Items.items() and Items.channels() instead
	#	return self._items[item]
	#def __contains__(self, item):
	#	return item in self._items

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
		obj = {"items": self._items, "channels": self._channels}
		try:
			with open(itemFile, "w") as f:
				yaml.safe_dump(obj, f)
			self._dirty = False
		except EnvironmentError as e:
			print("Unable to save item list.\nError: {}".format(e))
			raise
