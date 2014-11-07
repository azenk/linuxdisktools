__author__ = 'azenk'


class Controller(object):
	"""
	This class models a raid controller or hba
	"""

	def __init__(self):
		# Enclosure dict, keys are enclosure ids
		self._enclosures = dict()

	def enclosures(self):
		"""
		Iterator over all enclosures connected to this controller
		"""
		for enclosure_id, enclosure in iter(sorted(self._enclosures.iteritems())):
			yield enclosure

	def drives(self):
		"""
		Iterator over all drives connected to this controller
		"""
		for enclosure in self.enclosures():
			for drive in enclosure.drives():
				yield drive


class Enclosure(object):
	"""
	This class models a disk enclosure.  Typically this actually
	corresponds with one backplane.
	"""

	def __init__(self,enclosure_id=0):
		self.enclosure_id = enclosure_id
		# drives, keys are slot ids
		self._drives = dict()

	@property
	def enclosure_id(self):
		return self._enclosure_id

	@enclosure_id.setter
	def enclosure_id(self, value):
		if isinstance(value,basestring):
			value = int(value)
		self._enclosure_id = value

	def add_drive(self,drive):
		slot_id = drive.slot_number
		self._drives[slot_id] = drive

	def drives(self):
		"""
		Iterates over the drives that are connected to
		this enclosure
		"""
		for slot_number,drive in iter(sorted(self._drives.iteritems())):
			yield drive
	
	def __str__(self):
		return "Enclosure {0}: {1} drives".format(self.enclosure_id,len(self._drives))


class Drive(object):
	"""
	This class models a drive.
	"""


	def __init__(self,enclosure=None):
		self._enclosure = enclosure
		pass
		self._serial_number = None
		self._manufacturer = None
		self._wwn = None

	@property
	def slot_number(self):
		"""
		The number of the slot in the enclosure that this disk occupies
		"""
		return self._slot_number

	@slot_number.setter
	def slot_number(self, value):
		if isinstance(value,basestring):
			value = int(value)
		self._slot_number = value

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

	@property
	def model_number(self):
		return self._model_number

	@model_number.setter
	def model_number(self, value):
		self._model_number = value

	def healthy(self):
		"""
		:return: True if drive is healthy, False if some sort of corrective action is required
		"""
		return False

	def __str__(self):
		return "Drive {0} {5} {1} {3}:{4} Healthy? {2}".format(self.manufacturer,self.serial_number,self.healthy(),self._enclosure.enclosure_id,self.slot_number,self.model_number)
