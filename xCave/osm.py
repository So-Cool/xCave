import json
import numpy as np
import os
import requests
from itertools import tee, izip
from math import atan2, cos, radians, sin, sqrt
from os.path import basename, exists, isfile
from os import makedirs
from operator import itemgetter
from scipy.spatial import ConvexHull#, Delaunay
from sys import exit
from xml.etree import ElementTree

class OSMapi:
    """Get OSM files spanning in a regular grid through defined area using
    OpenStreet Maps API.
    Each frame has to span at least .00045*3 to maintain good resolution."""

    API_QUERY = "http://www.openstreetmap.org/api/0.6/map" + \
        "?bbox=%.6f,%.6f,%.6f,%.6f"

    SCALING_FACTOR = 0.00135

    def __init__(self, name, left, bottom, right, top, scaling_factor=None):
        if left > right:
            exit("left > right")
        if bottom > top:
            exit("bottom > top")
        self.name = name
        self.left = left
        self.bottom = bottom
        self.right = right
        self.top = top

        if scaling_factor is not None:
            self.SCALING_FACTOR = scaling_factor

        self.blocks = None

    global pairwise
    def pairwise(iterable):
        """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
        a, b = tee(iterable)
        next(b, None)
        return izip(a, b)

    def split_region(self):
        self.blocks = []
        y = np.abs(self.top - self.bottom)
        y_factor = np.ceil(y/self.SCALING_FACTOR)
        if y_factor != 1:
            y_steps = np.linspace(self.bottom, self.top, y_factor)
        else:
            y_steps = [self.bottom, self.top]
        x = np.abs(self.right - self.left)
        x_factor = np.ceil(x/self.SCALING_FACTOR)
        if x_factor != 1:
            x_steps = np.linspace(self.left, self.right, x_factor)
        else:
            x_steps = [self.left, self.right]
        for l, r in pairwise(x_steps):
            for b, t in pairwise(y_steps):
                self.blocks.append((l, b, r, t))

    def get_osm(self):
        if self.blocks:
            it = self.blocks
            iterator = ["_%d"%i for i in range(len(it))]
        else:
            it = [(self.left, self.bottom, self.right, self.top)]
            iterator = [""]
        for i, j in zip(it, iterator):
            print self.API_QUERY % (i[0], i[1], i[2], i[3])
            r = requests.get(self.API_QUERY % (i[0], i[1], i[2], i[3]))
            with open(self.name + j + ".osm", "w") as of:
                of.write(r.content)


class OSMinterface:
    KML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Document>
	<name>%(name)s</name>
	<open>1</open>
	<LookAt>
		<longitude>%(centreLon)s</longitude> <!--2.616655-->
		<latitude>%(centreLat)s</latitude> <!--51.461505-->
		<altitude>0</altitude>
		<heading>0</heading>
		<tilt>0</tilt>
		<range>%(range)s</range> <!--50 (InMeters)-->
	</LookAt>
	<StyleMap id="m_ylw-pushpin">
		<Pair>
			<key>normal</key>
			<styleUrl>#s_ylw-pushpin</styleUrl>
		</Pair>
		<Pair>
			<key>highlight</key>
			<styleUrl>#s_ylw-pushpin_hl</styleUrl>
		</Pair>
	</StyleMap>
	<Style id="s_ylw-pushpin">
		<IconStyle>
			<scale>1.1</scale>
			<Icon>
				<href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
			</Icon>
			<hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
		</IconStyle>
		<LineStyle>
			<color>00ffffff</color>
		</LineStyle>
		<PolyStyle>
			<color>00ffffff</color>
		</PolyStyle>
	</Style>
	<Style id="s_ylw-pushpin_hl">
		<IconStyle>
			<scale>1.3</scale>
			<Icon>
				<href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
			</Icon>
			<hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
		</IconStyle>
		<LineStyle>
			<color>00ffffff</color>
		</LineStyle>
		<PolyStyle>
			<color>00ffffff</color>
		</PolyStyle>
	</Style>
	<Placemark>
		<name>Region</name>
		<styleUrl>#m_ylw-pushpin</styleUrl>
		<Polygon>
			<tessellate>1</tessellate>
			<outerBoundaryIs>
				<LinearRing>
					<coordinates>
            %(maxlon)s,%(maxlat)s,0 <!-- -2.61643,51.46168,0 -->
            %(maxlon)s,%(minlat)s,0 <!-- -2.61643,51.46133,0 -->
            %(minlon)s,%(minlat)s,0 <!-- -2.61688,51.46133,0 -->
            %(minlon)s,%(maxlat)s,0 <!-- -2.61688,51.46168,0 -->
            %(maxlon)s,%(maxlat)s,0 <!-- -2.61643,51.46168,0 -->
					</coordinates>
				</LinearRing>
			</outerBoundaryIs>
		</Polygon>
	</Placemark>
</Document>
</kml>"""

    RANGE_FACTOR = 1.3 # 1.2
    MIN_SPAN_LON = 0.0004
    MIN_SPAN_LAT = 0.0004
    NUMBER_OF_CLOSEST_OBJECTS_TO_EXTRACT_BUILDING = 5
    NUMBER_OF_CLOSEST_OBJECTS_TO_EXTRACT_ROAD = 2

    def __init__(self, filename):
        # Map bounds
        self.bounds = None
        # Objects on the map
        self.objects = None
        # Mapping from object id to object type
        self.types = None
        # Mapping from id to coordinates; tuples of format (lat,lon)
        self.mapping = None

        if isfile(filename):
            self.filename = filename
        else:
            print "OSM file not given"
            exit(1)

    def read(self):
        """Read in OSM file into Python structure"""
        e = ElementTree.parse(self.filename).getroot()

        # Get map bounds
        self.bounds = e.find("bounds").attrib

        # Get mappings
        self.mapping = {}
        for i in e.iter("node"):
            self.mapping[i.attrib["id"]] = (i.attrib["lat"], i.attrib["lon"])

        # Get objects
        self.objects = {}
        self.types = {}
        for i in e.iter("way"):
            object_type = None
            for j in i.iter("tag"):
                # TODO: add more object types than *building* and *highway*
                if j.attrib["k"] == "building":
                    self.types[i.attrib["id"]] = "building"
                    object_type = True
                    break
                elif j.attrib["k"] == "highway":
                    self.types[i.attrib["id"]] = "highway"
                    object_type = True
                    break
            if object_type is None:
                continue

            self.objects[i.attrib["id"]] = []
            for j in i.iter("nd"):
                self.objects[i.attrib["id"]].append(j.attrib["ref"])

    def geo_distance(self, (lat1, lon1), (lat2, lon2)):
        """Calculate geo-distance between 2 points (in meters)."""
        # approximate radius of earth in meters
        R = 6373000.0

        lat1 = radians(lat1)
        lon1 = radians(lon1)
        lat2 = radians(lat2)
        lon2 = radians(lon2)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c

        return distance

    def save_object_to_klm(self, o, dirname="", max_lat=None, max_lon=None, max_range=None):
        """Save object as KLM file."""
        if dirname:
            dirname += "/"
        kml_filename = o+".kml"

        area = self.get_simple_bounding_box(o)
        area["name"] = o
        area["centreLat"], area["centreLon"] = self.get_centre(area)

        lon = abs(float(area["maxlon"]) - float(area["minlon"]))
        lat = abs(float(area["maxlat"]) - float(area["minlat"]))

        if max_lat is not None and max_lon is not None:
            # Maximise lat
            diff = (max_lat - lat) / 2.0
            area["minlat"] = str(float(area["minlat"]) - diff)
            area["maxlat"] = str(float(area["maxlat"]) + diff)
            # Maximise lon
            diff = (max_lon - lon) / 2.0
            area["minlon"] = str(float(area["minlon"]) - diff)
            area["maxlon"] = str(float(area["maxlon"]) + diff)
        else:
            # Enforce minimum size of the area
            if lon < self.MIN_SPAN_LON:
                diff = (self.MIN_SPAN_LON - lon) / 2.0
                lon = self.MIN_SPAN_LON
                area["minlon"] = str(float(area["minlon"]) - diff)
                area["maxlon"] = str(float(area["maxlon"]) + diff)
            if lat < self.MIN_SPAN_LAT:
                diff = (self.MIN_SPAN_LAT - lat) / 2.0
                lat = self.MIN_SPAN_LAT
                area["minlat"] = str(float(area["minlat"]) - diff)
                area["maxlat"] = str(float(area["maxlat"]) + diff)

        # 1m per each 0.00001 of difference in altitude or longitude
        l = max(lon, lat)
        if max_range is None:
            area["range"] = int(self.RANGE_FACTOR*int(l/0.000008))
        else:
            area["range"] = max_range

        kml = self.KML_TEMPLATE % area
        with open(dirname + kml_filename, "w") as kml_file:
            kml_file.write(kml)

    def save_klm_per_object(self, centroids=[]):
        """Save every object in the OSM file into KLM."""
        # Create a directory for the (closest) objects
        dirname = self.filename[:-4] + "_objects"
        if not exists(dirname):
            makedirs(dirname)

        # Get centers for each object
        object_centres = {}
        for o in self.types:
            cLat, cLon = self.get_centre(self.get_simple_bounding_box(o))
            object_centres[o] = (cLat, cLon)

        # Save objects nearest to centroids to KLM
        # 5 closest *buildings* and 2 *roads*
        if centroids:
            objects_to_extract = []
            for centroid in centroids:
                c_dist = []
                # Get distances form objects
                for o in object_centres:
                    c_dist.append(
                        (self.geo_distance(centroid, object_centres[o]), o)
                    )
                # Sort on distance
                c_dist.sort()

                # Select top NUMBER_OF_CLOSEST_OBJECTS_TO_EXTRACT_BUILDING and
                # ROAD
                b, r = 0, 0
                for i in c_dist:
                    if self.types[i[1]] == "building" and \
                       b < self.NUMBER_OF_CLOSEST_OBJECTS_TO_EXTRACT_BUILDING:
                        objects_to_extract.append(i[1])
                        b += 1
                    elif self.types[i[1]] == "highway" and \
                       b < self.NUMBER_OF_CLOSEST_OBJECTS_TO_EXTRACT_ROAD:
                        objects_to_extract.append(i[1])
                        r += 1
                    else:
                        break

            # Remove duplicates from the lsit
            objects_to_extract = list(set(objects_to_extract))

            max_range = -1.
            max_lon = -1.
            max_lat = -1.
            for o in objects_to_extract:
                area = self.get_simple_bounding_box(o)
                area["centreLat"], area["centreLon"] = self.get_centre(area)
                lon = abs(float(area["maxlon"]) - float(area["minlon"]))
                lat = abs(float(area["maxlat"]) - float(area["minlat"]))
                max_lat = max(max_lat, lat)
                max_lon = max(max_lon, lon)
            # 1m per each 0.00001 of difference in altitude or longitude
            l = max(max_lon, max_lat)
            max_range = int(self.RANGE_FACTOR*int(l/0.000008))

            # Memorise range, x and y sizes in JSON format
            with open(os.path.join(dirname, "region_spec.json"), "w") as region_spec:
                json.dump(
                {
                    "max_lat": max_lat,
                    "max_lon": max_lon,
                    "max_range": max_range
                },
                region_spec,
                sort_keys=True,
                indent=2,
                separators=(',', ': ')
                )

            for o in objects_to_extract:
                self.save_object_to_klm(o, dirname, max_lat, max_lon, max_range)
        # Save all objects to KLM
        else:
            for o in self.types:
                self.save_object_to_klm(o, dirname)

    def save_as_kml(self):
        "Save area extracted from OSM file into KML file."
        area = self.bounds.copy()

        area["centreLat"], area["centreLon"] = self.get_centre()

        # 1m per each 0.00001 of difference in altitude or longitude
        lon = abs(float(area["maxlon"]) - float(area["minlon"]))
        lat = abs(float(area["maxlat"]) - float(area["minlat"]))
        l = max(lon, lat)
        area["range"] = int(self.RANGE_FACTOR*int(l/0.000008))

        kml_filename = self.filename[:-3]+"kml"
        area["name"] = basename(kml_filename)

        kml = self.KML_TEMPLATE % area

        with open(kml_filename, "w") as kml_file:
            kml_file.write(kml)
    def id_to_coordinates(self, id):
        """Translate id into coordinates."""
        if id in self.mapping:
            return self.mapping[id]
        else:
            print "Unknown object id: ", id
            return None

    def get_centre(self, obj=None):
        if obj is None:
            obj = self.bounds
        c_lat = (float(obj["maxlat"])+float(obj["minlat"]))/2
        c_lon = (float(obj["maxlon"])+float(obj["minlon"]))/2
        return c_lat, c_lon

    def dist(self, a, b):
        a_lat, a_lon = a[0], a[1]
        b_lat, b_lon = b[0], b[1]
        return sqrt((a_lat-b_lat)**2 + (a_lon-b_lon)**2)

    def location_in_map(self, loc):
        """Is `loc` on this map?"""
        lat, lon = loc[0], loc[1]
        if float(self.bounds["minlat"]) < lat < float(self.bounds["maxlat"]) \
                and float(self.bounds["minlon"]) < lon < \
                    float(self.bounds["maxlon"]):
            return True
        else:
            return False

    def location_distance_from_map(self, loc):
        """Distance between `loc` and map's centre of mass."""
        c_lat, c_lon = self.get_centre()
        return self.dist(loc, (c_lat, c_lon))

    def location_in_object(self, loc):
        in_object = {}
        for i in self.objects:
            object_vertices = []
            for j in self.objects[i]:
                object_vertices.append(self.id_to_coordinates(j))

            # hull = ConvexHull(np.array(object_vertices))
            # if not isinstance(hull, Delaunay):
                # hull = Delaunay(hull)
            # in_hull = hull.find_simplex([loc])>=0
            # in_object[i] = in_hull[0]
            hull = ConvexHull(np.array(object_vertices))
            new_points = np.append(object_vertices, np.array([loc]), axis=0)
            new_hull = ConvexHull(new_points)
            if list(hull.vertices) == list(new_hull.vertices):
                in_object[i] = True
            else:
                in_object[i] = False

        return in_object

    def location_distance_from_objects(self, loc):
        """Distance between `loc` and the closes object in the map."""
        distances = {}
        for i in self.objects:
            object_centre_of_mass = None
            object_vertices = []
            for j in self.objects[i]:
                object_vertices.append((float(self.id_to_coordinates(j)[0]),
                                        float(self.id_to_coordinates(j)[1])))
            object_centre_of_mass = np.mean(object_vertices, axis=0)
            object_centre_of_mass = (object_centre_of_mass[0],
                                     object_centre_of_mass[1])
            distances[i] = self.dist(loc, object_centre_of_mass)
        return distances

    # TODO: do you prefer a complicated polygon or simple bounding box?
    def get_simple_bounding_box(self, id):
        """Produce simple (max/min) bounding box of a selected object."""
        coordinates = []
        for i in self.objects[id]:
            coordinates.append(self.id_to_coordinates(i))

        return {
            "minlat": min(coordinates, key=itemgetter(0))[0],
            "maxlat": max(coordinates, key=itemgetter(0))[0],
            "minlon": min(coordinates, key=itemgetter(1))[1],
            "maxlon": max(coordinates, key=itemgetter(1))[1]
        }

    def get_bounding_box(self, id):
        """Produce best fitted bounding box of a selected object; i.e. polygon
        generalisation's smallest surrounding rectangle."""
        # from qhull_2d import *
        # from min_bounding_rect import *
        # Get all blocks
        # blocks = []
        pass
