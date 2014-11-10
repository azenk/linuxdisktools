__author__ = 'azenk'

from base import Controller,Drive,Enclosure,DiskArray
import subprocess
from distutils.spawn import find_executable
import os.path,os,sys
import re

class MegaCLIResponse:

	normal_codes = [0x00]
	warning_codes = []
	code_strings = {
		0x00:"Command completed successfully",
		0x01:"Invalid command",
		0x02:"DCMD opcode is invalid",
		0x03:"Input parameters are invalid",
		0x04:"Invalid sequence number",
		0x05:"Abort isn't possible for the requested command",
		0x06:"Application 'host' code not found",
		0x07:"Application already in use - try later",
		0x08:"Application not initialized",
		0x09:"Given array index is invalid",
		0x0a:"Unable to add missing drive to array, as row has no empty slots",
		0x0b:"Some of the CFG resources conflict with each other or the current config",
		0x0c:"Invalid device ID / select-timeout",
		0x0d:"Drive is too small for requested operation",
		0x0e:"Flash memory allocation failed",
		0x0f:"Flash download already in progress",
		0x10:"Flash operation failed",
		0x11:"Flash image was bad",
		0x12:"Downloaded flash image is incomplete",
		0x13:"Flash OPEN was not done",
		0x14:"Flash sequence is not active",
		0x15:"Flush command failed",
		0x16:"Specified application doesn't have host-resident code",
		0x17:"LD operation not possibe - CC is in progress",
		0x18:"LD initialization in progress",
		0x19:"LBA is out of range",
		0x1a:"Maximum LDs are already configured",
		0x1b:"LD is not OPTIMAL",
		0x1c:"LD Rebuild is in progress",
		0x1d:"LD is undergoing reconstruction",
		0x1e:"LD RAID level is wrong for requested operation",
		0x1f:"Too many spares assigned",
		0x20:"Scratch memory not available - try command again later",
		0x21:"Error writing MFC data to SEEPROM",
		0x22:"Required HW is missing (i.e. Alarm or BBU)",
		0x23:"Item not found",
		0x24:"LD drives are not within an enclosure",
		0x25:"PD CLEAR operation is in progress",
		0x26:"Unable to use SATA(SAS) drive to replace SAS(SATA)",
		0x27:"Patrol Read is disabled",
		0x28:"Given row index is invalid",
		0x2d:"SCSI command done, but non-GOOD status was received-see mf.hdr.extStatus for SCSI_STATUS",
		0x2e:"IO request for MFI_CMD_OP_PD_SCSI failed - see extStatus for DM error",
		0x2f:"Matches SCSI RESERVATION_CONFLICT",
		0x30:"One or more of the flush operations failed",
		0x31:"FW real-time currently not set",
		0x32:"Command issues while FW in wrong state (i.e. GET RECON when op not active)",
		0x33:"LD is not OFFLINE - IO not possible",
		0x34:"Peer controller rejected request (possibly due to resource conflict)",
		0x35:"Unable to inform peer of communication changes (retry might be appropriate)",
		0x36:"LD reservation already in progress",
		0x37:"I2C errors were detected",
		0x38:"PCI errors occurred during XOR/DMA operation",
		0x39:"Diagnostics failed - see event log for details",
		0x3a:"Unable to process command as boot messages are pending",
		0x3b:"Returned in case if foreign configurations are imcomplete",
		0x3d:"Returned in case if a command is tried on unsupported hardware",
		0x3e:"CC scheduling is disabled",
		0x3f:"PD CopyBack operation is in progress",
		0x40:"Selected more than one PD per array",
		0x41:"Microcode update operation failed",
		0x42:"Unable to process command as drive security feature is not enabled",
		0x43:"Controller already has a lock key",
		0x44:"Lock key cannot be backed-up",
		0x45:"Lock key backup cannot be verified",
		0x46:"Lock key from backup failed verification",
		0x47:"Rekey operation not allowed, unless controller already has a lock key",
		0x48:"Lock key is not valid, cannot authenticate",
		0x49:"Lock key from escrow cannot be used",
		0x4a:"Lock key backup (pass-phrase) is required",
		0x4b:"Secure LD exist",
		0x4c:"LD secure operation is not allowed",
		0x4d:"Reprovisioning is not allowed",
		0x4e:"Drive security type (FDE or non-FDE) is not appropriate for requested operation",
		0x4f:"LD encryption type is not supported",
		0x50:"Cannot mix FDE and non-FDE drives in same array",
		0x51:"Cannot mix secure and unsecured LD in same array",
		0x52:"Secret key not allowed",
		0x53:"Physical device errors were detected",
		0x54:"Controller has LD cache pinned",
		0x55:"Requested operation is already in progress",
		0x56:"Another power state set operation is in progress",
		0x57:"Power state of device is not correct",
		0x58:"No PD is available for patrol read",
		0x59:"Controller resert is required",
		0x5a:"No EKM boot agent detected",
		0x5b:"No space on the snapshot repositiry VD",
		0x5c:"For consistency SET PiTs, some PiT creations might fail and some succeed",
		0xFF:"Invalid status - used for polling command completion",
	}

	_exit_code = None

	def __init__(self,output,exit_code=-1):
			if isinstance(exit_code,int):
				self._exit_code = exit_code
			elif isinstance(exit_code,str):
				self._exit_code = int(exit_code,16)
			else:
				raise Exception("Invalid Error Code Specified")
			
			self._output = output

	def get_error_string(self):
		try:
			if isinstance(self._exit_code,int) and self.code_strings.has_key(self._exit_code):
				return self.code_strings[self._exit_code]
			else:
				return "Unknown Error Code"
		except KeyError,e:
			return "Unknown Error Code"

	def is_error(self):
		return self._exit_code not in self.normal_codes and self._exit_code not in self.warning_codes

	def is_warning(self):
		return self._exit_code in self.warning_codes

	def is_normal(self):
		return self._exit_code in self.normal_codes

	def __iter__(self):
		tof = re.compile('^\r.*$\n',re.MULTILINE)
		blank_lines = re.compile('^\n+',re.MULTILINE)
		section_header = re.compile('^(.+)$\n *=+ *$\n',re.MULTILINE)
		key_val = re.compile('^([^:\n]+):(.*)$\n',re.MULTILINE)
		#key_val = re.compile('^([^:\n]+):(.*)\n(?!(^[^:\n]+:|\n))',re.MULTILINE)
		text = re.compile('^(.*)$\n',re.MULTILINE)

		offset = 0
		while offset < len(self._output)-1:
			tf = re.match(tof,self._output[offset:-1])
			if tf is not None:
				offset += len(tf.group(0))
				continue

			blanks = re.match(blank_lines,self._output[offset:-1])
			if blanks is not None:
				offset += len(blanks.group(0))
				continue

			sh = re.match(section_header,self._output[offset:-1])
			if sh is not None:
				offset += len(sh.group(0))
				yield ("Section Header", sh.group(1).strip())
				continue

			kv = re.match(key_val,self._output[offset:-1])
			if kv is not None:
				k = kv.group(1).strip()
				v = kv.group(2).strip()
				offset += len(kv.group(0))
				yield (k,v)
				continue

			t = re.match(text,self._output[offset:-1])
			if t is not None:
				offset += len(t.group(0))
				yield ("Text", t.group(1).strip())
				continue

			break


class LsiController(Controller):
	"""
	Models a lsi controller.
	Encapsulates the megaraid cli tools.
	"""

	def __init__(self,adapter_id=0,megacli=None):
		Controller.__init__(self)
		if megacli != None:
			self._megacli = megacli
		else:
			self._megacli = MegaCLI()
		
		self._adapter_id = adapter_id

		self.__read_data()

	def create_array(self,diskarray):
		if diskarray.raid_level == 10:
			mirrors = []
			if diskarray.drive_count % 2 != 0:
				raise Exception("Incorrect number of drives specified")

			mirror = []
			for disk in diskarray.drives():
				mirror.append(disk)
				if len(mirror) == 2:
					mirrors.append(mirror)
					mirror = []

			params = []
			for mirror in mirrors:
				arraynum = len(params)
				params.append("-Array{0}[{1}:{2},{3}:{4}]".format(
					arraynum,
					mirror[0].enclosure.enclosure_id,mirror[0].slot_number,
					mirror[1].enclosure.enclosure_id,mirror[1].slot_number))

			ret = self._megacli.call(['-CfgSpanAdd', '-R10'] + params +
									 ["WB","NoCachedBadBBU","-a{0}".format(self._adapter_id)])
			if ret.is_error():
				raise Exception("An error occurred while creating the array")

		elif diskarray.raid_level in [0, 1, 5, 6]:
			esids = map(lambda x: "{0}:{1}".format(x.enclosure.enclosure_id,x.slot_number),diskarray.drives())
			arraystr = ",".join(esids)
			ret = self._megacli.call(["-CfgLDAdd", "-R{0}[{1}]".format(diskarray.raid_level,arraystr),
								"WB","NoCachedBBU","-a{0}".format(self._adapter_id)])

			if ret.is_error():
				raise Exception("An error occurred while creating the array")

		else:
			raise Exception("Specified raid level is unsupported")

	def __read_data(self):
		self.__read_enclosure_data()
		#print(self._enclosures)
		self.__read_disk_data()
		self.__read_vd_data()

	def __read_vd_data(self):
		response = self._megacli.call(['-LDPDInfo',"-a{0}".format(self._adapter_id)])
		array = None
		enclosure_id = None
		for key, value in response:
			if key == "Virtual Drive":
				if array is not None:
					self._arrays[array.array_id] = array
				vd_id = int(re.match("([0-9]+)",value).group(1))
				array = DiskArray()
				array.array_id = vd_id
			elif key == "Enclosure Device ID":
				enclosure_id = int(value)
			elif key == "Slot Number":
				slot_id = int(value)
				array.add_drive(self._enclosures[enclosure_id]._drives[slot_id])
		
		self._arrays[array.array_id] = array

	def __read_enclosure_data(self):
		response = self._megacli.call(['-EncInfo',"-a{0}".format(self._adapter_id)])
		enclosure = None
		for key, value in response:
			if key == "Device ID":
				#print("Enclosure {0}".format(value))
				if enclosure is not None:
					self._enclosures[enclosure.enclosure_id] = enclosure

				value = int(value)

			
				if self._enclosures.has_key(value):
					enclosure = self._enclosures[value]
				else:
					enclosure = Enclosure(value)
			elif key == "Number of Slots":
				#print(int(value))
				enclosure.slots = int(value)
			elif key == "Partner Device ID":
				"""
				This is the id of a second expander on the same backplane.  
				Drives connected to one are connected to both
				"""
				pass
			elif key == "Product Identification":
				pass

		if enclosure is not None:
			self._enclosures[enclosure.enclosure_id] = enclosure
			
				

	def __read_disk_data(self):
		## Read Disk Data
		response = self._megacli.call(['-PDList',"-a{0}".format(self._adapter_id)])
		drive = None
		enclosure = None
		for key,value in response:
			if key == "Enclosure Device ID":
				value = int(value)

				if drive is not None and enclosure is not None:
					enclosure.add_drive(drive)
					self._enclosures[enclosure.enclosure_id] = enclosure
					enclosure = None

				if self._enclosures.has_key(value):
					enclosure = self._enclosures[value]
					#print("Found existing enclosure")
				else:
					enclosure = Enclosure(value)
					#print("Creating new enclosure")

				drive = Drive(enclosure)
			
			elif key == "Slot Number":
				drive.slot_number = value
				
			elif key == "WWN":
				drive.wwn = value

			elif key == "Firmware state":
				data = re.split(" *, *",value)
				drive.status = data[0]
				if data[0] == "Online":
					"""
 					A drive that can be accessed by the RAID controller and is part of the virtual 
					drive.
					"""
					pass	
				if data[0] == "Unconfigured Good":
					"""
					A drive that is functioning normally but is not configured as a part of a 
					virtual drive or as a hot spare
					"""
					pass	
				elif data[0] == "Hot Spare":
					"""
					A drive that is powered up and ready for use as a spare in case an online 
					drive fails.
					"""
					pass	
				elif data[0] == "Failed":
					"""
					A drive that was originally configured as Online or Hot Spare, but on which 
					the firmware detects an unrecoverable error.
					"""
					pass	
				elif data[0] == "Rebuild":
					"""
					 A drive to which data is being written to restore full redundancy for a virtual 
					 drive.
					"""
					pass	
				elif data[0] == "Unconfigured Bad":
					"""
					A drive on which the firmware detects an unrecoverable error; the drive was 
					Unconfigured Good or the drive could not be initialized.
					"""
					pass	
				elif data[0] == "Missing":
					"""
					A drive that was Online but which has been removed from its location.
					"""
					pass	
				elif data[0] == "Offline":
					"""
					A drive that is part of a virtual drive but which has invalid data as far as the 
					RAID configuration is concerned.
					When a virtual drive with cached data goes offline, the cache for the virtual 
					drive is discarded. Because the virtual drive is offline, the cache cannot be 
					saved
					"""
					pass	

				if len(data) > 1 and data[1] == "Spun Up":
					drive.spunup = True
				elif len(data) > 1 and data[1] == "Spun down":
					drive.spunup = False 

			
			elif key == "Inquiry Data":
				data = re.split(" +",value)
				if data[0] == "SEAGATE":
					drive.manufacturer = "Seagate"
					drive.model_number = data[1]
					drive.serial_number = data[2]
				elif data[0][0:2] == "WD":
					drive.manufacturer = "Western Digital"
					drive.model_number = data[1]
					drive.serial_number = data[0]
			else:
				# Some sort of catch all for non-specified attributes
				pass
		if drive is not None and enclosure is not None:
			enclosure.add_drive(drive)
			self._enclosures[enclosure.enclosure_id] = enclosure

class MegaCLI:
	def __init__(self):
		self._megacli_path = None

	@property
	def megacli_path(self):
		if self._megacli_path == None:
			"""
			Find MegaCLI on the system or throw exception
			"""
			def is_executable(fpath):
				return os.path.isfile(fpath) and os.access(fpath,os.X_OK)

			rpm64_path = "/opt/MegaRAID/MegaCli/MegaCli64"
			rpm32_path = "/opt/MegaRAID/MegaCli/MegaCli"

			fe64_path = find_executable("MegaCli64")
			fe32_path = find_executable("MegaCli")

			if fe64_path is not None:
				self._megacli_path = fe64_path
			elif fe32_path is not None:
				self._megacli_path = fe32_path
			elif is_executable(rpm64_path):
				self._megacli_path = rpm64_path
			elif is_executable(rpm32_path):
				self._megacli_path = rpm32_path

		return self._megacli_path

	@megacli_path.setter
	def megacli_path(self, value):
		self._megacli_path = value

	def call(self,args):
		"""
		Executes MegaCLI and returns output as a string
		:param args: A list of arguments to be passed to MegaCLI
		:return: Tuple of output string and MegaCLIError Object
		"""
		args.insert(0,self.megacli_path)
		p = subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		(out,err) = p.communicate()
		p.wait()
		return MegaCLIResponse(out,p.returncode)


	def discover(self):
		"""
		Runs MegaCLI to find all of the LSI controllers in the system
		:return: a list of all LSI controllers found in the system
		"""
		count = 0
		response = self.call(['-AdpCount'])
		for key,value in response:
			if key == "Controller Count":
				value = re.match("([0-9]+)", value).group(1)
				count = int(value)

		return map(lambda x: LsiController(adapter_id=x,megacli=self), range(count))

