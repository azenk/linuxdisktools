__author__ = 'azenk'


class Controller(object):
	"""
	This class models a raid controller or hba
	"""

	def __init__(self):
		# Enclosure dict, keys are enclosure ids
		self._enclosures = dict()
		# Array Dict, keys are array_id
		self._arrays = dict()

	def enclosures(self):
		"""
		Iterator over all enclosures connected to this controller
		"""
		for enclosure_id, enclosure in iter(sorted(self._enclosures.iteritems())):
			yield enclosure

	def arrays(self):
		for id, array in iter(sorted(self._arrays.iteritems())):
			yield array

	def drives(self):
		"""
		Iterator over all drives connected to this controller
		"""
		for enclosure in self.enclosures():
			for drive in enclosure.drives():
				yield drive

	def create_array(self,diskarray):
		"""
		Creates an array on the controller.  This method should be overridden by each controller type
		:param diskarray an instance of the DiskArray object that the controller will attempt to create
		"""
		pass

class DiskArray(object):
	"""
	This class models a storage array.  A collection of disks
	combined using some sort of raid technique.
	"""
	def __init__(self):
		self._array_id = None
		self._drives = []
		self._raid_level = None

	@property
	def raid_level(self):
		return self._raid_level

	@raid_level.setter
	def raid_level(self, value):
		self._raid_level = value

	@property
	def array_id(self):
		return self._array_id
	
	@array_id.setter
	def array_id(self, value):
		self._array_id = value

	def add_drive(self, drive):
		self._drives.append(drive)

	@property
	def drive_count(self):
		return len(self._drives)

	def drives(self):
		for drive in self._drives:
			yield drive

	def __str__(self):
		disks = map(lambda x: "{0}:{1}".format(x.enclosure.enclosure_id,x.slot_number),self._drives)
		return "Array {0} {1}".format(self.array_id,disks)

class Enclosure(object):
	"""
	This class models a disk enclosure.  Typically this actually
	corresponds with one backplane.
	"""

	def __init__(self,enclosure_id=0):
		self.enclosure_id = enclosure_id
		# drives, keys are slot ids
		self._drives = dict()
		self._slots = None

	@property
	def enclosure_id(self):
		return self._enclosure_id

	@enclosure_id.setter
	def enclosure_id(self, value):
		if isinstance(value,basestring):
			value = int(value)
		self._enclosure_id = value
	@property
	def slots(self):
		return self._slots

	@slots.setter
	def slots(self, value):
		#print("Setting number of slots {0}".format(value))
		self._slots = value

	def add_drive(self,drive):
		slot_id = drive.slot_number
		self._drives[slot_id] = drive

	def drive(self, slot_id):
		if self._drives.has_key(slot_id):
			return self._drives[slot_id]
		else:
			return None
		
	def drives(self):
		"""
		Iterates over the drives that are connected to
		this enclosure
		"""
		for slot_number,drive in iter(sorted(self._drives.iteritems())):
			yield drive
	
	def __str__(self):
		return "Enclosure {0}: {1} drives {2} slots".format(self.enclosure_id,len(self._drives),self.slots)


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
		self._predictive_failure_count = None
		self._other_errors = None
		self._media_errors = None
		self._raw_size_bytes = None
		self._coerced_size_bytes = None
		self._temperature_c = None

	@property
	def raw_size(self):
		return self._raw_size_bytes

	@raw_size.setter
	def raw_size(self, value):
		self._raw_size_bytes = value

	@property
	def coerced_size(self):
		return self._coerced_size_bytes

	@coerced_size.setter
	def coerced_size(self, value):
		self._coerced_size_bytes = value

	@property
	def temperature(self):
		return self._temperature_c

	@temperature.setter
	def temperature(self, value):
		self._temperature_c = value

	@property
	def other_errors(self):
		return self._other_errors

	@other_errors.setter
	def other_errors(self, value):
		self._other_errors = value

	@property
	def media_errors(self):
		return self._media_errors

	@media_errors.setter
	def media_errors(self, value):
		self._media_errors = value

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

	@property
	def status(self):
		try:
			return self._status
		except:
			return "Unknown"

	@property
	def spunup(self):
		try: 
			return self._spunup
		except:
			return None

	@spunup.setter
	def spunup(self, value):
		self._spunup = value

	@status.setter
	def status(self, value):
		self._status = value

	@property
	def enclosure(self):
		return self._enclosure

	@property
	def predictive_failure_count(self):
		return self._predictive_failure_count

	@predictive_failure_count.setter
	def predictive_failure_count(self, value):
		self._predictive_failure_count = value

	def healthy(self):
		"""
		:return: True if drive is healthy, False if some sort of corrective action is required
		"""
		healthy = True
		healthy = healthy and (self.media_errors is None or self.media_errors == 0)
		healthy = healthy and (self.other_errors is None or self.other_errors == 0)
		healthy = healthy and (self.predictive_failure_count is None or self.predictive_failure_count == 0)
		healthy = healthy and self.status in ["Online", "Unconfigured Good", "Hot Spare"]
		return healthy

	def __str__(self):
		return "Drive {0} {5} {1} {3}:{4} {2} Spun up? {6}".format(self.manufacturer,
																	self.serial_number,
																	"Healthy" if self.healthy() else "Unhealthy",
																	self.enclosure.enclosure_id,
																	self.slot_number,
																	self.model_number,
																	self.spunup)
