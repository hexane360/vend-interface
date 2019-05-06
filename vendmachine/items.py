import os
import yaml

class Items():
	def __init__(self, itemFile="items.yaml"):
		self.autosave = True
		self._itemFile = itemFile
		self.load(itemFile)

	def load(self, itemFile=None):
		if itemFile == None:
			itemFile = self._itemFile
		if os.path.exists(itemFile) and os.path.isfile(itemFile):
			print("Loading item list")
			with open(itemFile, "r") as f:
				try:
					self._items = yaml.safe_load(f)
				except yaml.YAMLError as e:
					print("Invalid YAML File: {}".format(itemFile))
					print("details: {}".format(e))
					raise
		else:
			print("Creating item list")
			self._items = {}
			with open(itemFile, "w") as f:
				yaml.safe_dump(self._items, f)

	def add(self, channel, price, motor, name=None, qty=0):
		if channel in self._items:
			raise ValueError("Item already exists")
		self._items[channel] = {
			"price": float(price),
			"name": str(name),
			"qty": int(qty),
			"motor": int(motor),
		}
		if self.autosave:
			self.save()

	def update(self, channel, price=None, motor=None, name=None, qty=None):
		if channel not in self._items:
			raise ValueError("Item does not exist")
		item = self._items[channel]
		if price != None:
			item["price"] = price
		if motor != None:
			item["motor"] = motor
		if name != None:
			item["name"] = name
		if qty != None:
			item["qty"] = qty
		if self.autosave:
			self.save()

	def items(self):
		return self._items

	def __len__(self):
		return len(_items)

	def __getitem__(self, item):
		return self._items[item]

	def __contains__(self, item):
		return item in self._items

	def save(self, itemFile=None):
		print("Saving item list")
		if itemFile == None:
			itemFile = self._itemFile
		with open(itemFile, "w") as f:
			yaml.safe_dump(self._items, f)
