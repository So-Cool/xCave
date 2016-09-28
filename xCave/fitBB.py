import glob
from PIL import Image, ImageDraw
from osm import OSMinterface

class FitBB():
    def __init__(self, filename, foldername=None):
        self.filename = filename
        if foldername is None:
            self.foldername = filename[:-4]
        else:
            self.foldername = foldername
        if self.foldername[-1] != "/":
            self.foldername += "/"

        self.images = None

    def read_images(self):
        """Read in all images captured for given OSM file."""
        self.images = {}
        for i in glob.glob(self.foldername + "*.jpg"):
            self.images[i] = Image.open(i)

    def plot_bb(self):
        """Fit bounding boxes into images."""
        o = OSMinterface(self.filename)
        o.read()
        map_centre = o.get_centre()

        image_size = self.images.items()[0].size
        image_centre = (image_size[0]/2, image_size[1]/2)

        for im in self.images:
            draw = ImageDraw.Draw(self.images[im])
            for ob in o.objects:
                for pt in
                draw.line((0, im.size[1], im.size[0], 0), fill=128, width=10)
            self.images[im].save(im[:-4]+".drawn", "jpeg")

    def get_translation(self, coordinates):
        """Translate image coordinates into pixel positions."""
        pass

    def cut_bb(self):
        """Cut out bounding boxes from images and save them into separate files
        using their unique identifiers (from openStreet maps)."""
        pass

class FitBBgui():
    """GUI for fixing the position of the bounding boxes."""

    def __init__(self):
        pass
