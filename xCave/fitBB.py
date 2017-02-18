import glob
import json
import os
import sys
from Tkinter import Tk, Label
from PIL import Image, ImageDraw, ImageTk
from PIL.ImageChops import offset

class Aligner:
    def __init__(self, master, region_folder, bounding_dimension=700):
        # Initialise data
        self.region_folder = os.path.abspath(region_folder)
        self.bounding_dimension = bounding_dimension
        self.clb_file = os.path.join(self.region_folder, \
                                     os.path.split(self.region_folder)[1]+".clb")
        self.images, self.size = self.read_images(self.region_folder)

        self.offset = {}
        self.global_x_offset = 0
        self.global_y_offset = 0

        middle = (int(self.size[0]/2.0), int(self.size[1]/2.0))
        square_half_side = int(0.025*max(self.size))
        self.square = [middle[0]-square_half_side, middle[1]-square_half_side, \
                       middle[0]+square_half_side, middle[1]+square_half_side]

        self.img_index = []
        for img in self.images.keys():
            time = os.path.basename(img).split("_")
            for t in time:
                if t.endswith(".jpg"):
                    time = t.strip(".jpg")
                    break
            self.img_index.append((int(time), img))
        self.img_index.sort()

        self.check_calibration()
        ########################################################################

        # Initialise GUI
        # Set window title
        self.master = master
        master.title("Aligner")

        # Set window size
        master.geometry("%dx%d+00+00" % (self.bounding_dimension, self.bounding_dimension))

        # self.label = Label(master, text="Welcome to Aligner!")
        # self.label.pack()

        self.label_index = 0
        self.set_photo()
        self.label = Label(master, image=self.photo)
        self.label.focus_set()
        self.label.bind("<Return>", self.cycle_images)
        self.label.bind("<Left>", self.left_key)
        self.label.bind("<Right>", self.right_key)
        self.label.bind("<Up>", self.up_key)
        self.label.bind("<Down>", self.down_key)
        self.label.bind("<q>", self.quit)
        self.label.pack()

    def set_photo(self):
        # Sort out the image
        tn = self.images[self.img_index[self.label_index][1]].copy()
        # Offset the image
        tn = offset(tn, self.global_x_offset, self.global_y_offset)
        draw = ImageDraw.Draw(tn, 'RGBA')
        draw.rectangle(self.square, (255, 0, 0, 125))
        del draw
        tn.thumbnail((self.bounding_dimension, self.bounding_dimension), Image.ANTIALIAS)
        self.photo = ImageTk.PhotoImage(tn)

    def cycle_images(self, event):
        self.offset[str(self.img_index[self.label_index][0])] = (self.global_x_offset, self.global_y_offset)
        self.save_calibration()
        self.label_index += 1
        if self.label_index >= len(self.img_index):
            self.master.quit()
        else:
            self.rebuild_image()

    def quit(self, event):
        self.master.quit()

    def left_key(self, event):
        self.global_x_offset -= 1
        self.rebuild_image()

    def right_key(self, event):
        self.global_x_offset += 1
        self.rebuild_image()

    def up_key(self, event):
        self.global_y_offset -= 1
        self.rebuild_image()

    def down_key(self, event):
        self.global_y_offset += 1
        self.rebuild_image()

    def rebuild_image(self):
        self.set_photo()
        self.label.config(image=self.photo)

    def read_images(self, img_folder):
        """Read in all images captured for given OSM file."""
        imgs = []
        for o in os.listdir(img_folder):
            d = os.path.join(img_folder, o)
            if os.path.isfile(d) and o.lower().endswith(".jpg"):
                imgs.append(d)

        images = {}
        for i in imgs:
            images[i] = Image.open(i)
        image_size = (images.values()[0].size)
        return images, image_size

    def save_calibration(self):
        with open(self.clb_file, "w") as calibration_file:
            json.dump(self.offset, calibration_file, sort_keys=True, indent=2, separators=(',', ': '))

    def check_calibration(self):
        if os.path.isfile(self.clb_file):
            print "Calibration file already exists:\n    %s" % self.clb_file
            with open(self.clb_file, "r") as calibration_file:
                self.offset = json.load(calibration_file)
                calib = [int(i) for i in self.offset.keys()]
            if len(self.img_index) != len(calib):
                rm = []
                print "Not all images are aligned."
                print "Aligning only the images with missing alignment values:"
                for i, j in self.img_index:
                    if i in calib:
                        rm.append((i,j))
                    else:
                        print ">    %s" % j
                for i in rm:
                    self.img_index.remove(i)
            else:
                print "All images are aligned."
                print "If you want to align all the images again please remove the *.clb file."
                print "If you want to align some of the images again please remove specific entry in the *.clb file."
                sys.exit()

class Fitter:
    def __init__(self, region_folder, calibration_file):
        self.region_folder = os.path.abspath(region_folder)
        if self.region_folder[-1] == "/":
            self.calibrated_folder = self.region_folder[-1] + "_calibrated"
        else:
            self.calibrated_folder = self.region_folder + "_calibrated"
        self.calibration_file = os.path.abspath(calibration_file)
        self.calibration = None

        self.load_calibration()

    def load_calibration(self, clb_file=None):
        if clb_file is None:
            clb_file = self.calibration_file
        with open(clb_file, "r") as calibration_file:
            self.calibration = json.load(calibration_file)

    def apply_calibration(self):
        """Apply calibration to all images."""
        # create calibrated dir
        if not os.path.exists(self.calibrated_folder):
            os.makedirs(self.calibrated_folder)

        for j in glob.glob(os.path.join(self.region_folder, "*.jpg")):
            filename = os.path.basename(j)
            time = filename.split("_")
            for t in time:
                if t.endswith(".jpg"):
                    time = t.strip(".jpg")
                    break

            if time in self.calibration:
                img = Image.open(j)
                img = offset(img, self.calibration[time][0], self.calibration[time][1])
                img.save(os.path.join(self.calibrated_folder, filename), "jpeg")

def gui(region_folder, bounding_dimension=700):
    root = Tk()
    my_gui = Aligner(root, region_folder, bounding_dimension)
    root.mainloop()
