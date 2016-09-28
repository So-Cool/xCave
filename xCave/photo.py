import glob
import numpy as np
from os.path import basename
from PIL import Image
from osm import OSMinterface

class PatchFinder:
    def __init__(self, osm_dir, image=None):
        self.image = image

        if osm_dir[-1] == "/":
            self.osm_dir = osm_dir
        else:
            self.osm_dir = osm_dir + "/"

        self.osms = None

    def load_osm_location_distances(self, image=None):
        self.image = image
        img_loc = self.get_gps_location(image)

        self.osms = {}
        for i in glob.glob(self.osm_dir + "*.osm"):
            f = OSMinterface(i)
            f.read()
            self.osms[basename(i)] = {}
            if f.location_in_map(img_loc):
                self.osms[basename(i)]["on_map"] = True
                if any(f.location_in_object(img_loc).values()):
                    self.osms[basename(i)]["in_object"] = \
                        f.location_in_object(img_loc)
                else:
                    self.osms[basename(i)]["in_object"] = False
                    self.osms[basename(i)]["dist_from_object"] = \
                        f.location_distance_from_objects(img_loc)
            else:
                self.osms[basename(i)]["on_map"] = False
                self.osms[basename(i)]["dist_from_map"] = \
                    f.location_distance_from_map(img_loc)

            f = None

    def print_location(self):
        # Is in any patch?
        maps = []
        for k in self.osms:
            if self.osms[k]["on_map"]:
                maps.append(k)

        patches = []
        for m in maps:
            if self.osms[m]["im_object"]:
                patches.append(m)

        if maps:
            obj_dist = []
            print "The photo", self.image, "is located in the following maps:"
            for m in maps:
                print  "    *", m
                for o in self.osms[m]["dist_from_object"]:
                    obj_dist.append((self.osms[m]["dist_from_object"][o], m, o))
            cp = min(obj_dist)

            if patches:
                print "It is in the following objects:"
                for m in patches:
                    for p in self.osms[m]["in_object"]:
                        if self.osms[m]["in_object"][p]:
                            print "    * map", m, "patch", p
            else:
                print "It is not in any particular object."
                print "The closes patch is:", cp[2], "on map", cp[1], \
                    "in distance", cp[0]
        else:
            print "The photo:", self.image, "is not in any of the specified \
                maps."
            dist_map = []
            for m in self.osms:
                dist_map.append((self.osms[m]["dist_from_map"], m))
            cm = min(dist_map)
            print "The closes map is:", cm[1], "within", cm[0], "distance."
        print "~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*"

    def get_gps_location(self, image=None):
        if image is None:
            f = self.image
        else:
            f = image
        return self.get_lat_lon(Image.open(f)._getexif())

    def get_lat_lon(self, info):
        get_float = lambda x: float(x[0]) / float(x[1])
        def convert_to_degrees(value):
            d = get_float(value[0])
            m = get_float(value[1])
            s = get_float(value[2])
            return d + (m / 60.0) + (s / 3600.0)

        try:
            gps_latitude = info[34853][2]
            gps_latitude_ref = info[34853][1]
            gps_longitude = info[34853][4]
            gps_longitude_ref = info[34853][3]
            lat = convert_to_degrees(gps_latitude)
            if gps_latitude_ref != "N":
                lat *= -1

            lon = convert_to_degrees(gps_longitude)
            if gps_longitude_ref != "E":
                lon *= -1
            return lat, lon
        except KeyError:
            return None
