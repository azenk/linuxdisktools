from disktools.lsi import MegaCLI,LsiController

def main():
	m = MegaCLI()
	print("Using MegaCLI from {0}".format(m.megacli_path))
	print("Getting adapter list...")
	#out,err = m.call(['-AdpAllInfo','-aALL'])
	lsi = LsiController(megacli=m)
	for drive in lsi.drives():
		print(drive)


if __name__ == "__main__":
	main()
