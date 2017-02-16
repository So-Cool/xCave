# xCave #
Google Earth Pro building extraction with history

## Installation ##
Required version of Python is 2. If you're using Python *virtual environments* do:
```
mkvirtualenv xCave
workon xCave
pip install -r requirements.xxx.txt
```

Otherwise do:
```
pip install --user -r requirements.xxx.txt
```

Where `xxx` is `osx` or `linux` depending on your operating system. If you're using Mac OS X installing *Xcode* first is required.

Ubuntu requires couple of additional packages:
```
sudo apt-get install scrot
sudo apt-get install python-tk
sudo apt-get install python-dev
sudo apt-get install python-imaging-tk
sudo apt-get install python-numpy
sudo apt-get install python-scipy
```

## Google Earth configuration ##
### Configure Google Earth interface ###
- Uncheck *Show tips at start-up*
- Make sure that *Search* tab is opened
- Uncheck all *Places*
- Uncheck all *Layers*

![](docs/ge_p.png "")

### Configure Google Earth speed ###
- In `Preferences --> Navigation` set *Fly-To speed* to maximum
- Now *maximize* Google Earth window to fit most of your screen space

![](docs/ge_fs.png "")

### Configure Google Earth save image ###
![](docs/ge_im.png "")
![](docs/ge_in.png "")

### Configure Google Earth history ###
When resizing the window make sure that history panel fits into the screen.

![](docs/ge_h.png "")

### Configure Google Earth exit ###
![](./docs/ge_q.png "")

## Usage ##
```
./xCave.py -h

./xCave.py -c

./xCave.py -o "85.307 27.702 85.312 27.705"

./xCave.py -k ./85.307_27.702_85.312_27.705.osm "(27.703625,85.309184); (27.703474,85.310344)"
# or ./xCave.py -k 85.307_27.702_85.312_27.705.osm
# or ./xCave.py -k ./osms/

./xCave.py -i 85.307_27.702_85.312_27.705_objects/111823094.kml
# or ./xCave.py -i 85.307_27.702_85.312_27.705_objects/

./xCave.py -g 85.307_27.702_85.312_27.705.osm _test_data/WP_20161010_075.jpg
# or ./xCave.py -g osm_test/ _test_data/WP_20161010_075.jpg
```
