__author__ = 'azenk'

import base
import subprocess
from distutils.spawn import find_executable
import os.path,os,sys
import re

class MegaCLIError:

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

	def __init__(self,exit_code=-1):
			if isinstance(exit_code,int):
				self._exit_code = exit_code
			elif isinstance(exit_code,str):
				self._exit_code = int(exit_code,16)
			else:
				raise Exception("Invalid Error Code Specified")

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

class LsiController(base.Controller):
	"""
	Models a lsi controller.
	Encapsulates the megaraid cli tools.
	"""
	_megacli_path = None

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

	@staticmethod
	def megacli(args):
		"""
		Executes MegaCLI and returns output as a string
		:param args: A list of arguments to be passed to MegaCLI
		:return: Tuple of output string and MegaCLIError Object
		"""
		args.insert(0,self._megacli_path)
		p = subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		(out,err) = p.communicate()
		p.wait()
		return (out,MegaCLIError(p.returncode))

	@staticmethod
	def parse_megacli_output(output):
		tof = re.compile('^\r.*$\n',re.MULTILINE)
		blank_lines = re.compile('^\n+',re.MULTILINE)
		section_header = re.compile('^\n(.+)$\n *=+ *$\n',re.MULTILINE)
		key_val = re.compile('^([^:\n]+):(.*)$\n',re.MULTILINE)
		text = re.compile('^(.*)$\n',re.MULTILINE)

		offset = 0
		while offset < len(output)-1:
			tf = re.match(tof,output[offset:-1])
			if tf is not None:
				print("Top")
				offset += len(tf.group(0))
				continue

			blanks = re.match(blank_lines,output[offset:-1])
			if blanks is not None:
				print("<Blank Lines>")
				offset += len(blanks.group(0))
				continue

			sh = re.match(section_header,output[offset:-1])
			if sh is not None:
				print("=========================%s================" % sh.group(1).strip())
				offset += len(sh.group(0))
				continue

			kv = re.match(key_val,output[offset:-1])
			if kv is not None:
				k = kv.group(1).strip()
				v = kv.group(2).strip()
				print("%s => %s (end)" % (k,v))
				offset += len(kv.group(0))
				continue

			t = re.match(text,output[offset:-1])
			if t is not None:
				print("text %s" % t.group(1))
				offset += len(t.group(0))
				continue

			break

		print("Done")
		sys.stdout.flush()

	@staticmethod
	def discover():
		"""
		Runs MegaCLI to find all of the LSI controllers in the system
		:return: a list of all LSI controllers found in the system
		"""
		return []

