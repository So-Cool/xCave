import glob
import os
import pyautogui
import subprocess
from time import sleep
from Quartz.CoreGraphics import CGEventCreateMouseEvent
from Quartz.CoreGraphics import CGEventPost
from Quartz.CoreGraphics import kCGEventMouseMoved
from Quartz.CoreGraphics import kCGEventLeftMouseDown
from Quartz.CoreGraphics import kCGEventLeftMouseUp
from Quartz.CoreGraphics import kCGMouseButtonLeft
from Quartz.CoreGraphics import kCGHIDEventTap

class GoogleEarthProCalibration:
    SETTINGS_FILE = "gep.calibration"

    POSITIONS_NAMES = [
        "google_earth_pro_offset",
        "save_image_icon",
        "save_image__map_options_menu",
        "save_image__map_options_menu__td",
        "save_image__map_options_menu__legend",
        "save_image__map_options_menu__scale",
        "save_image__map_options_menu__compass",
        "save_image__resolution",
        "save_image__resolution__maximum",
        "save_image__save_image_button",
        "history_button",
        "history_button__back",
        "history_button__forth",
        "close_button",
        "close_button__confirmation"
    ]

    def __init__(self):
        self.positions = {}
        for i in self.POSITIONS_NAMES:
            self.positions[i] = None

    def mouse_position(self):
        x, y = pyautogui.position()
        return (x, y)

    def memorise_locations(self):
        for k in self.POSITIONS_NAMES:
            print "Please move mouse over: *", k, "* and press *enter*."
            raw_input()
            self.positions[k] = self.mouse_position()

    def save_settings(self):
        if os.path.isfile(self.SETTINGS_FILE):
            print "Calibration file already exists; please remove " + \
                self.SETTINGS_FILE + " to calibrate again."
        else:
            with open(self.SETTINGS_FILE, "w") as sf:
                write_str = ""
                for k in self.positions:
                    write_str += k + ":" + str(self.positions[k]) + "\n"
                sf.write(write_str)

    def calibrate(self):
        self.memorise_locations()
        self.save_settings()

class GoogleEarthProInterface:
    X_SCALING = 1
    Y_SCALING = 1

    POSITIONS = {
        "google_earth_pro_offset": (0, 45), # (left, top) [px]
        "save_image_icon": (690, 9),
        "save_image__map_options_menu": (310, 40),
        "save_image__map_options_menu__td": (290, 100),
        "save_image__map_options_menu__legend": (290, 125),
        "save_image__map_options_menu__scale": (290, 150),
        "save_image__map_options_menu__compass": (290, 175),
        "save_image__resolution": (460, 40),
        "save_image__resolution__maximum": (460, 125),
        "save_image__save_image_button": (600, 40),
        "history_button": (485, 15),
        "history_button__back": (310, 100),
        "history_button__forth": (575, 100),
        "close_button": (15, -10),
        "close_button__confirmation": (665, 440)
    }

    # RETINA = True
    # SAVE_PNG="./save.png"

    SHORT_TIMEOUT = 0.5
    LONG_TIMEOUT = 5

    APP_LOCATION = "/Applications/Google\ Earth\ Pro.app"
    SAVE_LOCATION = "~/Desktop/"

    UPPER_HISTORY_BOUND = 30

    def mouseEvent(self, type, posx, posy):
        theEvent = CGEventCreateMouseEvent(None, type, (posx,posy), \
                                           kCGMouseButtonLeft)
        CGEventPost(kCGHIDEventTap, theEvent)

    def mousemove(self, posx,posy):
        self.mouseEvent(kCGEventMouseMoved, posx,posy)

    def mouseclick(self, posx,posy):
        # uncomment this line if you want to force the mouse
        # to MOVE to the click location first (I found it was not necessary).
        #mouseEvent(kCGEventMouseMoved, posx,posy);
        self.mouseEvent(kCGEventLeftMouseDown, posx,posy);
        self.mouseEvent(kCGEventLeftMouseUp, posx,posy);

    def offset(self, a):
        o = (self.X_SCALING*(a[0]+self.POSITIONS["google_earth_pro_offset"][0]),
             self.Y_SCALING*(a[1]+self.POSITIONS["google_earth_pro_offset"][1]))
        return o

    def __init__(self, filename):
        self.filename = filename
        # Save button location
        self.save = None
        self.history_counter = 0
        print "Please uncheck *Show tips at startup*"
        print "Please uncheck all *Places*"
        print "Please uncheck all *Layers*"
        print "Please make sure that *search* tab is opened"
        print "In *preferences->navigation* set *fly-to-speed* to maximum"
        print "Now Maximize it to fit your screen space"
        print "But make sure that history panel fits into screen..."
        print "and close it"
        raw_input("Press Enter to continue...")

        self.calibrate()

    def calibrate(self):
        """If calibration file exists load calibration settings; otherwise use
        default."""
        if os.path.isfile(GoogleEarthProCalibration.SETTINGS_FILE):
            print "Using config file"
            with open(GoogleEarthProCalibration.SETTINGS_FILE, "r") as gf:
                for l in gf:
                    cd = l.split(",")
                    self.POSITIONS[cd[0]] = (int(cd[1]), int(cd[2]))
        else:
            to_offset = [i for i in self.POSITIONS \
                         if i is not "google_earth_pro_offset"]
            for i in to_offset:
                self.POSITIONS[i] = self.offset(self.POSITIONS[i])

    def gep_open(self):
        subprocess.Popen(["/bin/bash", "-c", "open "+self.APP_LOCATION+" &"])
        sleep(self.LONG_TIMEOUT)

    def gep_close(self):
        close = self.POSITIONS["close_button"]
        self.mouseclick(*close)
        sleep(self.SHORT_TIMEOUT)

        confirm = self.POSITIONS["close_button__confirmation"]
        self.mouseclick(*confirm)
        sleep(self.SHORT_TIMEOUT)

    def gep_open_location(self):
        subprocess.Popen(["/bin/bash", "-c", "open "+self.filename+" &"])
        sleep(self.LONG_TIMEOUT)

    def gep_save_image_setup(self):
        # Open *Save Image* panel
        save_image = self.POSITIONS["save_image_icon"]
        self.mouseclick(*save_image)
        sleep(self.SHORT_TIMEOUT)

        # Change *Map Options*
        map_options = self.POSITIONS["save_image__map_options_menu"]
        self.mouseclick(*map_options)
        sleep(self.SHORT_TIMEOUT)

        # Uncheck *Title and Description*
        title_and_description = self.POSITIONS["save_image__map_options_menu__td"]
        self.mouseclick(*title_and_description)
        sleep(self.SHORT_TIMEOUT)

        # Uncheck *Legend*
        legend = self.POSITIONS["save_image__map_options_menu__legend"]
        self.mouseclick(*legend)
        sleep(self.SHORT_TIMEOUT)

        # Uncheck *Scale*
        scale = self.POSITIONS["save_image__map_options_menu__scale"]
        self.mouseclick(*scale)
        sleep(self.SHORT_TIMEOUT)

        # Uncheck *Compass*
        compass = self.POSITIONS["save_image__map_options_menu__compass"]
        self.mouseclick(*compass)
        sleep(self.SHORT_TIMEOUT)

        # Set *Resolution*
        resolution = self.POSITIONS["save_image__resolution"]
        self.mouseclick(*resolution)
        self.mouseclick(*resolution)
        sleep(self.SHORT_TIMEOUT)

        # Set *Resolution->Maximum*
        resolution_maximum = self.POSITIONS["save_image__resolution__maximum"]
        self.mouseclick(*resolution_maximum)
        sleep(self.SHORT_TIMEOUT)

        # TODO: do you need a screenschot of a date that the image was taken at

    def gep_save_image(self):
        # *Save image*
        save_image = self.POSITIONS["save_image__save_image_button"]
        self.mouseclick(*save_image)
        sleep(self.SHORT_TIMEOUT)

        # Give it a proper name
        pyautogui.typewrite(os.path.basename(self.filename) + "_" + \
                            str(self.history_counter))
        pyautogui.typewrite(["enter"])
        self.history_counter += 1
        sleep(self.LONG_TIMEOUT)

        # Locate save button if it has never been done before
        # if self.save is None:
            # save = pyautogui.locateOnScreen(self.SAVE_PNG)
            # self.save = pyautogui.center(save)
            # if self.RETINA:
                # self.save = (int(self.save[0]/2), int(self.save[1]/2))

        # Click save button
        # print self.save
        # self.mouseclick(*self.save)
        # sleep(self.SHORT_TIMEOUT)

    def gep_history_setup(self):
        # *History*
        history = self.POSITIONS["history_button"]
        self.mouseclick(*history)
        sleep(self.SHORT_TIMEOUT)

    def gep_history_back(self):
        # *History->left*
        left = self.POSITIONS["history_button__back"]
        self.mouseclick(*left)
        sleep(self.SHORT_TIMEOUT)

    def gep_history_forth(self):
        # TODO: untested
        # *History->right*
        right = self.POSITIONS["history_button__forth"]
        self.mouseclick(*right)
        sleep(self.SHORT_TIMEOUT)

    def gep_save_history(self):
        self.gep_open()
        self.gep_open_location()

        self.gep_save_image_setup()
        self.gep_save_image()

        self.gep_history_setup()
        self.gep_save_image()
        i = 0
        while not pyautogui.locateOnScreen("l.png") and \
              i < self.UPPER_HISTORY_BOUND:
            self.gep_history_back()
            self.gep_save_image()
            i += 1

        self.move_images()
        # self.gep_close()

    def move_images(self):
        dir_name = self.filename[:-4]
        while True:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
                break
            dir_name += "_"

        # Move files
        for i in glob.glob(os.path.expanduser(self.SAVE_LOCATION) + \
                           os.path.basename(self.filename) + "*" + ".jpg"):
            os.rename(i, dir_name+"/"+os.path.basename(i))


