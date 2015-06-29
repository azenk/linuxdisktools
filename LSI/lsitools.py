#!/usr/bin/env python

from disktools.lsi import MegaCLI, LsiController
from disktools.base import DiskArray
from argparse import ArgumentParser
import sys
import logging

from gelfHandler import gelfHandler

def main():
    p = ArgumentParser()
    p.add_argument('mode', choices=['drives','buildarrays'])
    p.add_argument('--graylog-host', '-g', dest="graylog_host", default=None)
    p.add_argument('--graylog-port', dest="graylog_port", type=int, default=12201)
    p.add_argument('--graylog-proto', dest="graylog_proto", choices=["TCP","UDP"], default="TCP")
    p.add_argument('--raid-level', '-r', dest="raid_level", type=int, choices=[0, 1, 5, 6, 10, 50, 60], default=6)
    p.add_argument('--drives-per-array','-c', dest="target_drive_count", type=int, default=None,
                   help="The target number of drives to include in each array")
    p.add_argument('--hotspares-per-array','-s', dest="hotspares_per_array", type=int, default=1,
                   help="The number of hotspares that should be allocated per array that is built, all are global")
    p.add_argument('--bad-only', '-b', action='store_true', dest='bad_only', default=False,
                   help="Only display devices with health issues")
    args = p.parse_args()

    logger = logging.getLogger('lsitools')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s -%(gelfProps)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if args.graylog_host != None:
    try:
        gHandler = gelfHandler(host=args.graylog_host,port=args.graylog_port,proto=args.graylog_proto)
        gHandler.setLevel(logging.DEBUG)
        logger.addHandler(gHandler)
        logger.debug("Graylog handler added successfully", extra={"gelfProps": dict()})
    except Exception, e:
        logger.warn("Unable to setup gelf logging %s" % e, extra={"gelfProps": dict()})

    logger.debug("Application started, logging configured.", extra={"gelfProps": dict()})

    m = MegaCLI()
    if args.mode == "drives":
        m = MegaCLI()
        # print("Using MegaCLI from {0}".format(m.megacli_path))
        # print("Getting adapter list...")
        # out,err = m.call(['-AdpAllInfo','-aALL'])
        for lsi in m.discover():
            for drive in lsi.drives():
                props = dict()
                props["_drive_enclosure"] = drive.enclosure.enclosure_id
                props["_drive_slot"] = drive.slot_number
                props["_drive_health"] = drive.health
                props["_drive_serial"] = drive.serial_number
                props["_drive_model"] = drive.model_number
                props["_drive_manufacturer"] = drive.manufacturer 
                props["_drive_raw_size"] = drive.raw_size
                props["_drive_status"] = drive.status
                props["_drive_temperature"] = drive.temperature
                props["_drive_media_errors"] = drive.media_errors
                props["_drive_other_errors"] = drive.other_errors
                props["_drive_predictive_failure_count"] = drive.predictive_failure_count
                if drive.health < 100.0:
                    logger.error("Failing drive", extra={"gelfProps": props})
                elif not args.bad_only:
                    logger.info("Normal drive",extra={"gelfProps": props})

                # for a in lsi.arrays():
                # print(a)
                #
                # for enclosure in lsi.enclosures():
                # print(enclosure)
    elif args.mode == "buildarrays":
        array_n = args.target_drive_count
        raid_lvl = args.raid_level
        hotspare_n = args.hotspares_per_array
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
