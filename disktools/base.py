__author__ = 'azenk'


class Controller:
	"""
	This class models a raid controller or hba
	"""
	def enclosures(self):
		"""
		Iterator over all enclosures connected to this controller
		"""
		pass

	def drives(self):
		"""
		Iterator over all drives connected to this controller
		"""
		for enclosure in self.enclosures():
			for drive in enclosure.drives():
				yield drive


class Enclosure:
	"""
	This class models a disk enclosure.  Typically this actually
	corresponds with one backplane.
	"""
	_enclosure_id = None

	@property
	def enclosure_id(self):
		return self._enclosure_id

	@enclosure_id.setter
	def set_enclosure_id(self,enclosure_id):
		self._enclosure_id = enclosure_id

	def drives(self):
		"""
		Iterates over the drives that are connected to
		this enclosure
		"""
		pass


class Drive:
	"""
	This class models a drive.
	"""

	_serial_number = None
	_manufacturer = None
	_wwn = None


	@property
	def serial_number(self):
		return self._serial_number

	@serial_number.setter
	def serial_number(self, value):
		self._serial_number = value

	@property
	def manufacturer(self):
		return self._manufacturer

	@manufacturer.setter
	def manufacturer(self, value):
		self._manufacturer = value

	@property
	def wwn(self):
		return self._wwn

	@wwn.setter
	def wwn(self, value):
		self._wwn = value

	def healthy(self):
		"""
		:return: True if drive is healthy, False if some sort of corrective action is required
		"""
		return False
