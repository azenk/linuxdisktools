from disktools.lsi import MegaCLI,LsiController

def main():
	m = MegaCLI()
	#print("Using MegaCLI from {0}".format(m.megacli_path))
	#print("Getting adapter list...")
	#out,err = m.call(['-AdpAllInfo','-aALL'])
	for lsi in m.discover():
		for drive in lsi.drives():
			if drive.healthy() < 10.0:
				print(drive)
		
		#for a in lsi.arrays():
			#print(a)
		#
		##for enclosure in lsi.enclosures():
			#print(enclosure)


if __name__ == "__main__":
	main()
