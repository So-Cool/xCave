import glob
import Tkinter as tk
from PIL import Image, ImageDraw, ImageTk
from osm import OSMinterface

class FitBB():
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
        map_h_diff = abs(float(self.osm.bounds["maxlat"]) - float(self.osm.bounds["minlat"]))
        map_w_h_ratio = float(map_w_diff)/float(map_h_diff)

        map_w_middle = float(self.osm.bounds["minlon"]) + map_w_diff/float(2)
        map_h_middle = float(self.osm.bounds["minlat"]) + map_h_diff/float(2)

        img_w_diff = self.image_size[0]
        img_h_diff = self.image_size[1]
        img_w_h_ratio = float(img_w_diff)/float(img_h_diff)

        if map_w_h_ratio < img_w_h_ratio:
            print "here"
            # memorise scale for points
            w = map_h_diff * img_w_diff / float(img_h_diff)
            w /= 2
            self.bounding_h = (float(self.osm.bounds["minlat"]), float(self.osm.bounds["maxlat"]))
            self.bounding_w = (map_w_middle-w, map_w_middle+w) # min, max
        elif map_w_h_ratio > img_w_h_ratio:
            self.bounding_dimmension = "W"
            # memorise scale for points
            h = map_w_diff * img_h_diff / float(img_w_diff)
            h /= 2
            self.bounding_w = (float(self.osm.bounds["minlon"]), float(self.osm.bounds["maxlon"]))
            self.bounding_h = (map_h_middle-h, map_h_middle+h)
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
        x1_pixels = abs((self.bounding_w[0]-bbox[0][0])/(self.bounding_w[1]-self.bounding_w[0])) * self.image_size[1]
        y1_pixels = abs((self.bounding_h[0]-bbox[0][1])/(self.bounding_h[1]-self.bounding_h[0])) * self.image_size[0]
        #
        x2_pixels = abs((self.bounding_w[0]-bbox[1][0])/(self.bounding_w[1]-self.bounding_w[0])) * self.image_size[1]
        y2_pixels = abs((self.bounding_h[0]-bbox[1][1])/(self.bounding_h[1]-self.bounding_h[0])) * self.image_size[0]
        # Recalculate max and min for this dimension
        # use scale to return image cooridnates
        return [(x1_pixels, y1_pixels), (x2_pixels, y2_pixels)]

    def pixelise_map_objects(self):
        boxes = {}
        for i in self.osm.types:
            bbox = self.osm.get_simple_bounding_box(i)
            bbox = [(float(bbox["mminlon"]),float(bbox["minlat"])),
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

    def cut_bb(self):
        """Cut out bounding boxes from images and save them into separate files
        using their unique identifiers (from openStreet maps)."""
       # width, height = im.size
       # w, h = yourImage.size
       # yourImage.crop((0, 30, w, h-30)).save(...)
        pass

    def read_user_reshape(self):
        """Read in and save user parameters: x offset, y offset, and scale."""
        pass

#    def plot_bb(self):
#        """Fit bounding boxes into images."""
#        o = OSMinterface(self.filename)
#        o.read()
#        map_centre = o.get_centre()
#
#        image_size = self.images.items()[0].size
#        image_centre = (image_size[0]/2, image_size[1]/2)
#
#        for im in self.images:
#            draw = ImageDraw.Draw(self.images[im])
#            for ob in o.objects:
#                for pt in
#                draw.line((0, im.size[1], im.size[0], 0), fill=128, width=10)
#            self.images[im].save(im[:-4]+".drawn", "jpeg")

class FitBBgui(tk.Tk):
    """GUI for fixing the position of the bounding boxes."""

    def __init__(self):
        tk.Tk.__init__(self)
        self.x = self.y = 0
        self.canvas = tk.Canvas(self, width=512, height=512, cursor="cross")
        self.canvas.pack(side="top", fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.rect = None

        self.start_x = None
        self.start_y = None


        self._draw_image()


    def _draw_image(self):
         self.im = Image.open('./resource/lena.jpg')
         self.tk_im = ImageTk.PhotoImage(self.im)
         self.canvas.create_image(0,0,anchor="nw",image=self.tk_im)



    def on_button_press(self, event):
        # save mouse drag start position
        self.start_x = event.x
        self.start_y = event.y

        # create rectangle if not yet exist
        #if not self.rect:
        self.rect = self.canvas.create_rectangle(self.x, self.y, 1, 1, fill="black")

    def on_move_press(self, event):
        curX, curY = (event.x, event.y)

        # expand rectangle as you drag the mouse
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)



    def on_button_release(self, event):
        pass
