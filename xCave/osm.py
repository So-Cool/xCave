import numpy as np
from math import sqrt
from os.path import basename, isfile
from operator import itemgetter
from scipy.spatial import ConvexHull#, Delaunay
from sys import exit
from xml.etree import ElementTree

class OSMapi:
    """Get OSM files spanning in a regular grid through defined area using
    OpenStreet Maps API."""
    def __init__(self):
        pass
        "http://www.openstreetmap.org/api/0.6/map?bbox=0,0,0.1,0.1"

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
            self.objects[i.attrib["id"]] = []
            for j in i.iter("nd"):
                self.objects[i.attrib["id"]].append(j.attrib["ref"])
            for j in i.iter("tag"):
                # TODO: add more object types than *building*
                if j.attrib["k"] == "building":
                    self.types[i.attrib["id"]] = j.attrib["k"]

    def save_as_kml(self):
        "Save area extracted from OSM file into KML file."
        area = self.bounds.copy()

        area["centreLat"], area["centreLon"] = self.get_centre()

        # 1m per each 0.00001 of difference in altitude or longitude
        lon = abs(float(area["maxlon"]) - float(area["minlon"]))
        lat = abs(float(area["maxlat"]) - float(area["minlat"]))
        l = max(lon, lat)
        area["range"] = int(1.1*int(l/0.000008))

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

    def get_centre(self):
        c_lat = (float(self.bounds["maxlat"])+float(self.bounds["minlat"]))/2
        c_lon = (float(self.bounds["maxlon"])+float(self.bounds["minlon"]))/2
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
            "mminlon": min(coordinates, key=itemgetter(1))[1],
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
