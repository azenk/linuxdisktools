#!/usr/bin/env python

from disktools.lsi import MegaCLI, LsiController
from disktools.base import DiskArray
from argparse import ArgumentParser
import sys

def main():
    p = ArgumentParser()
    p.add_argument('mode', choices=['drives','buildarrays'])
    p.add_argument('--raid-level', '-r', dest="raid_level", type=int, choices=[0, 1, 5, 6, 10, 50, 60], default=6)
    p.add_argument('--drives-per-array','-c', dest="target_drive_count", type=int, default=None,
                   help="The target number of drives to include in each array")
    p.add_argument('--hotspares-per-array','-s', dest="hotspares_per_array", type=int, default=1,
                   help="The number of hotspares that should be allocated per array that is built, all are global")
    args = p.parse_args()

    m = MegaCLI()
    if args["mode"] == "drives":
        m = MegaCLI()
        # print("Using MegaCLI from {0}".format(m.megacli_path))
        # print("Getting adapter list...")
        # out,err = m.call(['-AdpAllInfo','-aALL'])
        for lsi in m.discover():
            for drive in lsi.drives():
                if drive.health < 100.0:
                    print(drive)

                # for a in lsi.arrays():
                # print(a)
                #
                # for enclosure in lsi.enclosures():
                # print(enclosure)
    elif args["mode"] == "buildarrays":
        array_n = args["target_drive_count"]
        raid_lvl = args["raid_level"]
        hotspare_n = args["hotspares_per_array"]
        m = MegaCLI()
        for lsi in m.discover():
            for enclosure in lsi.enclosures():
                if array_n == None:
                    if enclosure.slots >= 10:
                        arrays = enclosure.slots / 10
                        remainder = enclosure.slots % 10
                        array_n = 10 + remainder / arrays - hotspare_n
                    else:
                        array_n = enclosure.slots - hotspare_n

                count = 0
                a = DiskArray()
                a.raid_level = raid_lvl
                for drive in enclosure.drives():
                    if drive.status == "Unconfigured(good)":
                        if count % (array_n + hotspare_n) > 0:
                            a.add_drive(drive)
                        else:
                            lsi.create_global_hotspare(drive)
                        count += 1
                    if count % (array_n + hotspare_n) == 0:
                        lsi.create_array(a)
                        a = DiskArray()
                        a.raid_level = raid_lvl

                if a.drive_count > 0:
                    lsi.create_array(a)




if __name__ == "__main__":
    main()
