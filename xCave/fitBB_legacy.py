from osm import OSMinterface

class FitBB:
    """
    # Cut test bboxes
    f = FitBB("bs8.osm")
    f.read_images()
    f.get_bounding_dimension()
    bboxes = f.pixelise_map_objects()
    f.plot_images(bboxes)
    """
    def __init__(self, region_name, region_folder=None):
        """Read in OSM file describing the region and the folder containing
        historical imagery of this region."""
        self.region_name = region_name
        if region_folder is None:
            self.region_folder = region_name[:-4]
        else:
            self.region_folder = region_folder
        if self.region_folder[-1] != "/":
            self.region_folder += "/"

        # read in region size and objects from the osm file
        self.osm = OSMinterface(self.region_name)
        self.osm.read()
        # self.bounds = o.bounds
        # self.objects = o.objects
        # self.types = o.types
        # self.mapping = o.mapping

        self.bounding_h =  None
        self.bounding_w =  None

        # Images placeholder
        self.images = None
        self.image_size = None

    def get_bounding_dimension(self):
        # Figure out which dimension is the limiting one
        map_w_diff = abs(float(self.osm.bounds["maxlon"]) - float(self.osm.bounds["minlon"]))
        # 2* because one is 0--180 and the other 0--360
        map_h_diff = abs(float(self.osm.bounds["maxlat"]) - float(self.osm.bounds["minlat"]))
        map_w_h_ratio = float(map_w_diff)/(2*float(map_h_diff))
        print map_w_h_ratio

        map_w_middle = float(self.osm.bounds["minlon"]) + map_w_diff/float(2)
        map_h_middle = float(self.osm.bounds["minlat"]) + map_h_diff/float(2)

        img_w_diff = self.image_size[0]
        img_h_diff = self.image_size[1]
        img_w_h_ratio = float(img_w_diff)/float(img_h_diff)
        print img_w_h_ratio

        if map_w_h_ratio < img_w_h_ratio:
            # memorise scale for points
            w = (2*1.3*map_h_diff * img_w_diff) / float(img_h_diff)
            w /= 2
            self.bounding_h = (float(self.osm.bounds["minlat"]), float(self.osm.bounds["maxlat"]))
            self.bounding_w = (map_w_middle-w, map_w_middle+w) # min, max
            self.bounding = 'w'
        elif map_w_h_ratio > img_w_h_ratio:
            self.bounding_dimmension = "W"
            # memorise scale for points
            h = 1.3*map_w_diff * img_h_diff / float(img_w_diff)
            h /= 2
            self.bounding_w = (float(self.osm.bounds["minlon"]), float(self.osm.bounds["maxlon"]))
            self.bounding_h = (map_h_middle-h, map_h_middle+h)
            self.bounding = 'h'
        elif map_w_h_ratio == img_w_h_ratio:
            self.bounding_h = (float(self.osm.bounds["minlat"]), float(self.osm.bounds["maxlat"]))
            self.bounding_w = (float(self.osm.bounds["minlon"]), float(self.osm.bounds["maxlon"]))

    def read_images(self):
        """Read in all images captured for given OSM file."""
        self.images = {}
        for i in glob.glob(self.region_folder + "*.jpg"):
            self.images[i] = Image.open(i)

        self.image_size = (self.images.values()[0].size)

    # TODO: #, x_offset=None, y_offset=None, scale=None
    def get_translation(self, bbox):
        """Translate image coordinates into pixel positions. Input and output
	    are of the form: [(x1, y1), (x2, y2)], where (x1, y1) is top left
	    corner and (x2, y2) is bottom right corner."""
        x1_pixels = abs((self.bounding_w[0]-bbox[0][0])/(self.bounding_w[1]-self.bounding_w[0])) * self.image_size[0]
        y1_pixels = abs((self.bounding_h[0]-bbox[0][1])/(self.bounding_h[1]-self.bounding_h[0])) * self.image_size[1]
        #
        x2_pixels = abs((self.bounding_w[0]-bbox[1][0])/(self.bounding_w[1]-self.bounding_w[0])) * self.image_size[0]
        y2_pixels = abs((self.bounding_h[0]-bbox[1][1])/(self.bounding_h[1]-self.bounding_h[0])) * self.image_size[1]
        # Recalculate max and min for this dimension
        # use scale to return image cooridnates
        return [(x1_pixels, y1_pixels), (x2_pixels, y2_pixels)]

    def pixelise_map_objects(self):
        boxes = {}
        for i in self.osm.types:
            bbox = self.osm.get_simple_bounding_box(i)
            bbox = [(float(bbox["minlon"]),float(bbox["minlat"])),
                    (float(bbox["maxlon"]),float(bbox["maxlat"]))]
            boxes[i] = self.get_translation(bbox)
        return boxes

    def plot_images(self, box=None):
        """Plot images one by one; wait for a key stroke to display the next
        one."""
        tn_size = (500, 500)
        for img in self.images:
            root = tk.Tk() # Toplevel()
            root.title(img)
            root.geometry("%dx%d+00+00" % tn_size)

            tn = self.images[img].copy()
            if box is not None:
                draw = ImageDraw.Draw(tn, 'RGBA')
                for b in box:
                    draw.rectangle(box[b], (255, 0, 0, 125))
                del draw

            # Resize for displaying purposes
            tn.thumbnail(tn_size, Image.ANTIALIAS)

            tk_img = ImageTk.PhotoImage(tn)
            panel = tk.Label(root, image=tk_img )
            panel.pack(side="bottom", fill="both", expand="yes")
            root.mainloop()

            print "Please close the image window to continue..."

