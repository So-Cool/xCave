#! /usr/bin/env python2

import argparse
import ConfigParser
import os
import sys
from xCave.fitBB import ElementOffset
from xCave.googleEarth import GoogleEarthProCalibration
from xCave.googleEarth import GoogleEarthProInterface
from xCave.helpers import parse_config
from xCave.helpers import curate_tuples
from xCave.helpers import str2tuple
from xCave.osm import OSMapi
from xCave.osm import OSMinterface
from xCave.photo import PatchFinder

CONFIG_FILE = "./xCave.conf"

# command line arguments parser
parser = argparse.ArgumentParser(description='Google Earth Pro imagery extractor.')
parser_group1 = parser.add_mutually_exclusive_group()
parser_group1.add_argument('-c', '--calibrate', required=False, dest="calibrate", \
                           default=False, action='store_true', \
                           help=('Calibrate Google Earth Pro interface.'))
parser_group1.add_argument('-i', '--imagery', required=False, dest="imagery", \
                           type=str, nargs=1, default="", action='store', \
                           help=('Download Google Earth Pro imagery from specified KML file or a folder with KML files.'))
parser_group1.add_argument('-o', '--osm', required=False, dest="osm", \
                           type=str, nargs=1, default="", action='store', \
                           help=('Download region file from OpenStreet Maps. This option requires a string of 4 values restricting the region: "left bottom top right".'))
parser_group1.add_argument('-k', '--klm', required=False, dest="klm", \
                           type=str, nargs="+", default="", action='store', \
                           help=('Convert given OSM file into KLM file. The first argument is a path to an OSM file or a directory containing OSM files. The second optional argument is a list of points of interest; 5 objects close to each point will be extracted and saved as a separate KLM file e.g. "(27.703625,85.309184); (27.703474, 85.310344)".'))
parser_group1.add_argument('-g', '--geolocate', required=False, type=str, \
                           nargs=2, dest="geolocate", default="", action='store', \
                           help=('Geolocate image in an OSM file or a set of OSM files. The first argument is OSM file or a folder containing OSM files; the second argument is an image to be geo-located.'))

# configuration parser
conf = ConfigParser.ConfigParser()
conf.read(CONFIG_FILE)
config = parse_config(conf)

if __name__ == "__main__":
    args = parser.parse_args()

    # Calibrate Google Earth Pro
    if args.calibrate:
        if config.get("GoogleEarthPro", {}).get("calibrated", False):
            print "Google Earth is already calibrated"
            y = None
            while y != 'y' and y != 'n':
                y = raw_input("Do you want to discard existing calibration? [y/n]\n> ").lower()
            if y == 'y':
                print "Discarding Google Earth calibration"
                conf.set("GoogleEarthPro", "calibrated", False)
                with open(CONFIG_FILE, "w") as cfw:
                    conf.write(cfw)
                print "Please run calibration again"
            else:
                print "Quitting"
        else:
            gep_path = config.get("GoogleEarthPro", {}).get("executable_path", None)
            gui = config.get("GoogleEarthPro", {}).get("gui", None)
            version = config.get("GoogleEarthPro", {}).get("version", None)
            c = GoogleEarthProCalibration(gep_path, version, gui)
            gep_calibration = c.calibrate()
            conf.set("GoogleEarthPro", "calibrated", True)
            for i in gep_calibration:
                conf.set("GoogleEarthCalibration", i, gep_calibration[i])
            with open(CONFIG_FILE, "w") as cfw:
                conf.write(cfw)

    # Download Google Earth History
    if args.imagery:
        # Load settings
        gep_path = config.get("GoogleEarthPro", {}).get("executable_path", None)
        save_location = config.get("GoogleEarthPro", {}).get("save_location", "~/Desktop")
        calibration = curate_tuples(config.get("GoogleEarthCalibration", {}))
        if not config.get("GoogleEarthPro", {}).get("calibrated", False) or \
           not calibration:
            sys.exit("Google Earth not calibrated.\nExiting...")
        history_bound = config.get("GoogleEarthPro", {}).get("history_bound", 10)
        selected_resolution = config.get("GoogleEarthPro", {}).get("resolution", "current")
        help_message = config.get("GoogleEarthPro", {}).get("help_message", True)
        version = config.get("GoogleEarthPro", {}).get("version", None)

        g = GoogleEarthProInterface(args.imagery[0], gep_path, version, \
                                    save_location, calibration, history_bound, \
                                    selected_resolution, help_message)
        g.gep_save_history()

    # Get OSM file of specified region
    if args.osm:
        # Decide whether to split
        osm_range = args.osm[0].split()
        osm_name = "_".join(osm_range)
        osm_range = [float(i) for i in osm_range]

        a = OSMapi(osm_name, *osm_range)
        split_osm = config.get("xCave", {}).get("split_osm", False)
        if split_osm:
            a.split_region()
        a.get_osm()

    # Save as klm
    if len(args.klm) > 0:
        def str2lot(s):
            ss = s.split(";")
            ss = [str2tuple(i, "float") for i in ss]
            return ss
        def parse_osm(f, r):
            o = OSMinterface(f)
            o.read()
            if r is None:
                o.save_as_kml()
            else:
                o.save_klm_per_object(r)

        if len(args.klm) > 2:
            sys.exit("Error: only 2 arguments are expected!")
        elif len(args.klm) == 2:
            klm_name = args.klm[0]
            regions = str2lot(args.klm[1])
        else:
            klm_name = args.klm[0]
            regions = None

        if os.path.isfile(klm_name):
            parse_osm(klm_name, regions)
        elif os.path.isdir(klm_name):
            files = os.listdir(klm_name)
            files = [os.path.join(klm_name,i) for i in files if i.endswith(".osm")]
            for f in files:
                parse_osm(f, regions)

    # Geolocate image(s)
    if len(args.geolocate) == 2:
        p = PatchFinder(args.geolocate[0]) # p = PatchFinder("./", "./osm.osm")
        p.load_osm_location_distances(args.geolocate[1])
        p.print_location()
