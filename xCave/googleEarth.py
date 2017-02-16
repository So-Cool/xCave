import glob
import os
import pyautogui
import subprocess
import Tkinter
from PIL import Image
from pynput.keyboard import Key, Listener
from sys import exit
from time import sleep

class GoogleEarthProCalibration:
    POSITIONS_NAMES = [
        "google_earth_pro_offset",
        "save_image_icon",
        "save_image__map_options_menu",
        "save_image__map_options_menu__td",
        "save_image__map_options_menu__legend",
        "save_image__map_options_menu__scale",
        "save_image__map_options_menu__compass",
        "save_image__resolution",
        "save_image__resolution__current",
        "save_image__resolution__maximum",
        "save_image__save_image_button",
        "history_button",
        "history_button__back",
        "history_button__forth",
        "history_window__top_left",
        "history_window__bottom_right",
        "close_button",
        "close_button__confirmation"
    ]

    def on_press(self, key):
        pass
        # print('{0} pressed'.format(key))
    def on_release(self, key):
        pass
        # print('{0} release'.format(key))
        if key == Key.ctrl:
            # Stop listener
            return False

    def __init__(self, gep_path, version, gui=True):
        self.gep_path = gep_path
        self.dummy = "./dummy.kml"
        self.gui = gui
        self.version = version
        self.positions = {}
        for i in self.POSITIONS_NAMES:
            self.positions[i] = None

    def mouse_position(self):
        x, y = pyautogui.position()
        return (x, y)

    def memorise_locations(self):
        for k in self.POSITIONS_NAMES:
            if self.version == "standard" and k.startswith("save_image__"):
                continue
            if self.gui:
                root = Tkinter.Tk()
                label = Tkinter.Message(root, text="Please move mouse over: *%s* and press left or right *control*."%k, relief=Tkinter.RAISED)
                label.pack()
                root.mainloop()
                # Collect events until released
                with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
                    listener.join()
            else:
                print "Please move mouse over: *", k, "* and press *enter*."
                raw_input()
            self.positions[k] = self.mouse_position()

    def open_gep(self):
        subprocess.Popen(["/bin/bash", "-c", self.gep_path+" "+self.dummy+" &"])

    def save_settings(self, settings_file):
        with open(settings_file, "w") as sf:
            write_str = ""
            for k in self.positions:
                write_str += k + "," + str(self.positions[k][0]) + "," + \
                    str(self.positions[k][1]) + "\n"
            sf.write(write_str)

    def calibrate(self, settings_file=None):
        if settings_file is not None:
            if os.path.isfile(self.settings_file):
                print "Calibration file already exists; please remove " + \
                    self.settings_file + " to calibrate again."
                exit(1)
            self.open_gep()
            self.memorise_locations()
            self.save_settings()
        else:
            self.open_gep()
            self.memorise_locations()
            return self.positions

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
        "save_image__resolution__current": (460, 75),
        "save_image__resolution__maximum": (460, 125),
        "save_image__save_image_button": (600, 40),
        "history_button": (485, 15),
        "history_button__back": (310, 100),
        "history_button__forth": (575, 100),
        "history_window__top_left": (270, 80),
        "history_window__bottom_right": (610, 140),
        "close_button": (15, -10),
        "close_button__confirmation": (665, 440)
    }

    # RETINA = True
    # SAVE_PNG="./save.png"

    DATA_PREVIOUS = None
    DATA_CURRENT = None

    SHORT_TIMEOUT = 1.0
    LONG_TIMEOUT = 5

    def offset(self, a):
        o = (self.X_SCALING*(a[0]+self.POSITIONS["google_earth_pro_offset"][0]),
             self.Y_SCALING*(a[1]+self.POSITIONS["google_earth_pro_offset"][1]))
        return o

    def __init__(self, filename, gep_path, version, save_location="~/Desktop/", \
                 calibration=None, history_bound=None, selected_resolution="maximum", \
                 help_message=True, scaling=1):
        self.gep_path = gep_path
        self.save_location = save_location
        self.selected_resolution = selected_resolution
        self.version = version

        if scaling:
            self.scaling = scaling
        else:
            self.scaling = 1

        if history_bound is None:
            self.upper_history_bound = 30
        else:
            self.upper_history_bound = history_bound

        if os.path.isfile(filename):
            self.filename = [filename]
            self.dirname = ""
        elif os.path.isdir(filename):
            self.dirname = os.path.abspath(filename)
            self.filename = []
            for i in glob.glob(os.path.join(self.dirname,"*.kml")):
                self.filename.append(i)
        else:
            print "Unknown file type!"
            exit()
        # Save button location
        self.save = None
        self.history_counter = 0
        if help_message:
            print "Please uncheck *Show tips at startup*"
            print "Please uncheck all *Places*"
            print "Please uncheck all *Layers*"
            print "Please make sure that *search* tab is opened"
            print "In *preferences->navigation* set *fly-to-speed* to maximum"
            print "Now Maximize it to fit your screen space"
            print "But make sure that history panel fits into screen..."
            print "and close it"
            raw_input("Press Enter to open Google Earth Pro...")
            self.gep_open()
            raw_input("Press Enter to continue (once the above steps have been completed and Google Earth has been closed)...")
        self.calibrate(calibration)

    def calibrate(self, calibration_dict=None):
        """If calibration file exists load calibration settings; otherwise use
        default."""
        if calibration_dict is not None:
            for i in self.POSITIONS:
                if self.version == "standard" and i.startswith("save_image__"):
                    continue
                self.POSITIONS[i] = calibration_dict[i]
        else:
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
        subprocess.Popen(["/bin/bash", "-c", self.gep_path+" &"])
        sleep(self.LONG_TIMEOUT)

    def gep_close(self):
        close = self.POSITIONS["close_button"]
        pyautogui.click(*close, button='left')
        sleep(self.SHORT_TIMEOUT)

        confirm = self.POSITIONS["close_button__confirmation"]
        pyautogui.click(*confirm, button='left')
        sleep(self.SHORT_TIMEOUT)

    def gep_open_location(self, location=None):
        if location is None:
            location = self.filename[0]
        subprocess.Popen(["/bin/bash", "-c", self.gep_path+" "+location+" &"])
        sleep(self.LONG_TIMEOUT)

    def gep_save_image_setup(self):
        # Skip setup if using standart Google Earth version
        if self.version == "standard":
            return

        # Open *Save Image* panel
        save_image = self.POSITIONS["save_image_icon"]
        pyautogui.click(*save_image, button='left')
        sleep(self.SHORT_TIMEOUT)

        # Change *Map Options*
        map_options = self.POSITIONS["save_image__map_options_menu"]
        pyautogui.click(*map_options, button='left')
        sleep(self.SHORT_TIMEOUT)

        # Uncheck *Title and Description*
        title_and_description = self.POSITIONS["save_image__map_options_menu__td"]
        pyautogui.click(*title_and_description, button='left')
        sleep(self.SHORT_TIMEOUT)

        # Uncheck *Legend*
        legend = self.POSITIONS["save_image__map_options_menu__legend"]
        pyautogui.click(*legend, button='left')
        sleep(self.SHORT_TIMEOUT)

        # Uncheck *Scale*
        scale = self.POSITIONS["save_image__map_options_menu__scale"]
        pyautogui.click(*scale, button='left')
        sleep(self.SHORT_TIMEOUT)

        # Uncheck *Compass*
        compass = self.POSITIONS["save_image__map_options_menu__compass"]
        pyautogui.click(*compass, button='left')
        sleep(self.SHORT_TIMEOUT)

        # Set *Resolution*
        resolution = self.POSITIONS["save_image__resolution"]
        pyautogui.click(*resolution, button='left')
        pyautogui.click(*resolution, button='left')
        sleep(self.SHORT_TIMEOUT)

        # Set *Resolution->Maximum* or *current
        if self.selected_resolution == "maximum":
            resolution_type = self.POSITIONS["save_image__resolution__maximum"]
        else:
            resolution_type = self.POSITIONS["save_image__resolution__current"]
        pyautogui.click(*resolution_type, button='left')
        sleep(self.SHORT_TIMEOUT)

    def save_date_window(self, filename=None):
        if filename is None:
            filename = self.filename[0]
        window = (self.scaling*self.POSITIONS["history_window__top_left"][0],
                  self.scaling*self.POSITIONS["history_window__top_left"][1],
                  self.scaling*self.POSITIONS["history_window__bottom_right"][0],
                  self.scaling*self.POSITIONS["history_window__bottom_right"][1])
        im = pyautogui.screenshot(region=window)
        im.save(os.path.join(
                    os.path.expanduser(self.save_location),
                    os.path.basename(filename)[:-4] + "_date_" + str(self.history_counter) + ".jpg")
            , "JPEG")

    def gep_save_image(self, filename=None):
        if filename is None:
            filename = self.filename[0]
        # Save data
        self.save_date_window(filename)
        # *Save image*
        if self.version == "standard":
            save_image = self.POSITIONS["save_image_icon"]
        else: # pro
            save_image = self.POSITIONS["save_image__save_image_button"]
        pyautogui.click(*save_image, button='left')
        sleep(self.SHORT_TIMEOUT)

        # Give it a proper name
        name = os.path.basename(filename)[:-4] + "_" + str(self.history_counter)
        pyautogui.typewrite(name)
        pyautogui.typewrite(["enter"])
        self.history_counter += 1

        sleep(self.LONG_TIMEOUT/2.0)
        self.DATA_PREVIOUS = self.DATA_CURRENT
        self.DATA_CURRENT = Image.open(os.path.expanduser(os.path.join(self.save_location, name+".jpg")))

        sleep(self.LONG_TIMEOUT)

        # Locate save button if it has never been done before
        # if self.save is None:
            # save = pyautogui.locateOnScreen(self.SAVE_PNG)
            # self.save = pyautogui.center(save)
            # if self.RETINA:
                # self.save = (int(self.save[0]/2), int(self.save[1]/2))

        # Click save button
        # print self.save
        # pyautogui.click(*self.save, button='left')
        # sleep(self.SHORT_TIMEOUT)

    def gep_history_setup(self):
        # *History*
        history = self.POSITIONS["history_button"]
        pyautogui.click(*history, button='left')
        sleep(self.SHORT_TIMEOUT)

    def gep_history_close(self):
        history = self.POSITIONS["history_button"]
        pyautogui.click(*history, button='left')
        self.history_counter = 0
        self.DATA_CURRENT = None
        sleep(self.SHORT_TIMEOUT)

    def gep_history_back(self):
        # *History->left*
        left = self.POSITIONS["history_button__back"]
        pyautogui.click(*left, button='left')
        sleep(self.SHORT_TIMEOUT)

    def gep_history_forth(self):
        # TODO: untested
        # *History->right*
        right = self.POSITIONS["history_button__forth"]
        pyautogui.click(*right, button='left')
        sleep(self.SHORT_TIMEOUT)

    def gep_save_history(self):
        self.gep_open()
        sleep(self.LONG_TIMEOUT)
        self.gep_save_image_setup()
        for f in self.filename:
            self.gep_open_location(f)
            sleep(self.SHORT_TIMEOUT)
            self.gep_save_image(f)

            sleep(self.SHORT_TIMEOUT)
            self.gep_history_setup()
            sleep(self.SHORT_TIMEOUT)
            self.gep_save_image(f)
            i = 0
            # while not pyautogui.locateOnScreen("xCave/l.png") and \
            while self.DATA_CURRENT != self.DATA_PREVIOUS and \
                i < self.upper_history_bound:
                self.gep_history_back()
                sleep(self.SHORT_TIMEOUT)
                self.gep_save_image(f)
                i += 1

            self.move_images(f)
            self.gep_history_close()
            sleep(self.LONG_TIMEOUT)
        self.gep_close()

    def move_images(self, filename=None):
        if filename is None:
            filename = os.path.basename(self.filename[0])
        dir_name = self.dirname
        if dir_name:
            dir_name = os.path.join(dir_name, os.path.basename(filename)[:-4])
        else:
            dir_name = os.path.abspath(filename)[:-4]
        date_dir_name = dir_name + "_dates"
        while True:
            if not os.path.exists(dir_name) and not os.path.exists(date_dir_name):
                os.makedirs(dir_name)
                os.makedirs(date_dir_name)
                break
            dir_name += "_"
            date_dir_name += "_"

        # Move date files
        for i in glob.glob(os.path.join(os.path.expanduser(self.save_location),
                                        os.path.basename(filename)[:-4] + "_date_*.jpg")):
            os.rename(i, os.path.join(date_dir_name,os.path.basename(i)))
        # Move imagery files
        for i in glob.glob(os.path.join(os.path.expanduser(self.save_location),
                                        os.path.basename(filename)[:-4] + "*.jpg")):
            os.rename(i, os.path.join(dir_name,os.path.basename(i)))
