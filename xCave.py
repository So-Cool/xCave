#! /usr/bin/env python2

import argparse
import ConfigParser
import os
import sys
from xCave.helpers import parse_config
try:
    from xCave.googleEarth import GoogleEarthProCalibration
    CALIBRATION = True
except ImportError, e:
    print >> sys.stderr, "Calibration packages are missing."
    print >> sys.stderr, e
    print >> sys.stderr, 40*"~-"
    CALIBRATION = False
try:
    from xCave.googleEarth import GoogleEarthProInterface
    from xCave.helpers import curate_tuples
    INTERFACE = True
except ImportError, e:
    print >> sys.stderr, "Google Earth Interface packages are missing."
    print >> sys.stderr, e
    print >> sys.stderr, 40*"~-"
    INTERFACE = False
try:
    from xCave.osm import OSMapi
    OSM = True
except ImportError, e:
    print >> sys.stderr, "OSM API packages are missing."
    print >> sys.stderr, e
    print >> sys.stderr, 40*"~-"
    OSM = False
try:
    from xCave.helpers import str2tuple
    from xCave.osm import OSMinterface
    KLM = True
except ImportError, e:
    print >> sys.stderr, "KLM packages are missing."
    print >> sys.stderr, e
    print >> sys.stderr, 40*"~-"
    KLM = False
try:
    from xCave.photo import PatchFinder
    GEO = True
except ImportError, e:
    print >> sys.stderr, "Geolocation packages are missing."
    print >> sys.stderr, e
    print >> sys.stderr, 40*"~-"
    GEO = False
try:
    from xCave.fitBB import gui
    GUI = True
except ImportError, e:
    print >> sys.stderr, "GUI packages are missing."
    print >> sys.stderr, e
    print >> sys.stderr, 40*"~-"
    GUI = False
try:
    from xCave.fitBB import Fitter
    ALI = True
except ImportError, e:
    print >> sys.stderr, "Image alignment packages are missing."
    print >> sys.stderr, e
    print >> sys.stderr, 40*"~-"
    ALI = False

CONFIG_FILE = "./xCave.conf"

# command line arguments parser
parser = argparse.ArgumentParser(description='Google Earth Pro imagery extractor.')
parser_group1 = parser.add_mutually_exclusive_group()
parser_group1.add_argument('-c', '--calibrate', required=False, dest="calibrate", \
                           default=False, action='store_true', \
                           help=('Calibrate Google Earth Pro interface.'))
parser_group1.add_argument('-i', '--imagery', required=False, dest="imagery", \
                           type=str, nargs="+", default="", action='store', \
                           help=('Download Google Earth Pro imagery from specified KML file or a folder with KML files.\nIf second argument (integer) is provided the imagery will be downloaded from given image number onwards (steps down the Google Earth history).'))
parser_group1.add_argument('-o', '--osm', required=False, dest="osm", \
                           type=str, nargs=1, default="", action='store', \
                           help=('Download region file from OpenStreet Maps. This option requires a string of 4 values restricting the region: "left bottom top right".'))
parser_group1.add_argument('-k', '--klm', required=False, dest="klm", \
                           type=str, nargs="+", default="", action='store', \
                           help=('Convert given OSM file into KLM file. The first argument is a path to an OSM file or a directory containing OSM files. The second optional argument is a list of points of interest; 5 objects close to each point will be extracted and saved as a separate KLM file e.g. "(27.703625,85.309184); (27.703474, 85.310344)".'))
parser_group1.add_argument('-g', '--geolocate', required=False, type=str, \
                           nargs=2, dest="geolocate", default="", action='store', \
                           help=('Geolocate image in an OSM file or a set of OSM files. The first argument is OSM file or a folder containing OSM files; the second argument is an image to be geo-located.'))
parser_group1.add_argument('-a', '--align', required=False, dest="align", \
                           type=str, nargs=1, default="", action='store', \
                           help=('Invoke GUI to align images in given directory.'))
parser_group1.add_argument('-p', '--apply', required=False, dest="apply", \
                           type=str, nargs=2, default="", action='store', \
                           help=('Apply alignment to images in given directory (the first argument is *alignment file* and the second is *directory* with images).'))

# configuration parser
conf = ConfigParser.ConfigParser()
conf.read(CONFIG_FILE)
config = parse_config(conf)

if __name__ == "__main__":
    args = parser.parse_args()

    # Calibrate Google Earth Pro
    if args.calibrate and CALIBRATION:
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
            help_message = config.get("GoogleEarthPro", {}).get("help_message", True)
            gep_path = config.get("GoogleEarthPro", {}).get("executable_path", None)
            gui = config.get("GoogleEarthPro", {}).get("gui", None)
            version = config.get("GoogleEarthPro", {}).get("version", None)
            os = config.get("GoogleEarthPro", {}).get("os", "linux")
            c = GoogleEarthProCalibration(gep_path, version, gui, os, help_message)
            gep_calibration = c.calibrate()
            conf.set("GoogleEarthPro", "calibrated", True)
            for i in gep_calibration:
                conf.set("GoogleEarthCalibration", i, gep_calibration[i])
            with open(CONFIG_FILE, "w") as cfw:
                conf.write(cfw)
        sys.exit()

    # Download Google Earth History
    if len(args.imagery)>0 and INTERFACE:
        # Load settings
        gep_path = config.get("GoogleEarthPro", {}).get("executable_path", None)
        save_location = config.get("GoogleEarthPro", {}).get("save_location", "~/Desktop")
        calibration = curate_tuples(config.get("GoogleEarthCalibration", {}))
        if not config.get("GoogleEarthPro", {}).get("calibrated", False) or \
           not calibration:
            sys.exit("Google Earth not calibrated.\nExiting...")
        history_bound = config.get("GoogleEarthPro", {}).get("history_bound", 10)
        selected_resolution = config.get("GoogleEarthPro", {}).get("resolution", "current")
        version = config.get("GoogleEarthPro", {}).get("version", None)
        scaling = config.get("GoogleEarthPro", {}).get("retina_scaling", 1)
        os = config.get("GoogleEarthPro", {}).get("os", "linux")
        typewrite_interval = config.get("GoogleEarthPro", {}).get("typewrite_interval", 0.25)

        if len(args.imagery) == 1:
            start_point = 0
        elif len(args.imagery) > 1:
            try:
                start_point = int(args.imagery[1])
            except:
                print "Second argument (integer) not recognised: [%s]." % args.imagery[1]
                sys.exit(1)

        g = GoogleEarthProInterface(args.imagery[0], gep_path, version, \
                                    save_location, calibration, history_bound, \
                                    selected_resolution, \
                                    scaling, os, typewrite_interval, start_point)
        g.gep_save_history()
        sys.exit()

    # Get OSM file of specified region
    if args.osm and OSM:
        # Decide whether to split
        osm_range = args.osm[0].split()
        osm_name = "_".join(osm_range)
        osm_range = [float(i) for i in osm_range]

        a = OSMapi(osm_name, *osm_range)
        split_osm = config.get("xCave", {}).get("split_osm", False)
        if split_osm:
            a.split_region()
        a.get_osm()
        sys.exit()

    # Save as klm
    if len(args.klm) > 0 and KLM:
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
        sys.exit()

    # Geolocate image(s)
    if len(args.geolocate) == 2 and GEO:
        p = PatchFinder(args.geolocate[0]) # p = PatchFinder("./", "./osm.osm")
        p.load_osm_location_distances(args.geolocate[1])
        p.print_location()
        sys.exit()

    # Align images
    if args.align and GUI:
        bounding_dimension = config.get("aligner", {}).get("max_dim", 700)
        gui(args.align[0], bounding_dimension)
        sys.exit()

    # Apply alignment
    if args.apply and ALI:
        a = Fitter(args.apply[1], args.apply[0])
        a.apply_calibration()
        sys.exit()

    parser.print_help()
