=====================
MapSlicer Application
=====================
https://wiki.osgeo.org/wiki/MapSlicer

MapSlicer is a graphical application for online map publishing. Your map can create overlay of standard maps like OpenStreetMap, Google Maps, Yahoo Maps or Bing Maps and can be also visualized in 3D by Google Earth. The only thing you have to do for publishing the map is to upload the automatically generated directory with tiles into your webserver.

MapSlicer is an open-source application, distributed under the New BSD License.
It can run on several platforms, including Linux, Microsoft Windows and Apple Mac OS X.

You can download the source code from the repository at https://github.com/kalxas/mapslicer

Requirements
------------
In case you would like to run the application from the code you need:
- Python 2.5
- wxPython 2.8+
- GDAL 1.6+

The application can be started by running:

$ python mapslicer.py

Or depending on the installation method there should be a program icon in the programs menu.

Packaging
---------
The packaging scripts and instructions are in the directory /deploy/.


Development
-----------
Development of the project happens on GitHub. Pull Requests are welcome :)

We would like to thank Petr Pridal - Klokan for his contribution of the original MapTiler project.

Sponsors of MapTiler/GDAL2Tiles:

	* http://www.davidrumsey.com - supported improvement of Google Earth SuperOverlay rendering
	* http://www.nic.cz/ and http://www.nic.cz/vip/ - Vyvíjej, Inovuj, Programuj
	* http://www.brgm.fr/ - Bureau des Recherches Geologiques et Minières - French Geological Survey Office
	* http://www.oldmapsonline.org/ - Moravian Library Brno, Czech Ministry of Culture
	* http://code.google.com/soc/ - Google Summer of Code 2007, 2008 (GDAL2Tiles utility) - OSGeo and Google Inc.

Huge thanks to the team of http://www.gdal.org/ and also people from http://www.osgeo.org/ .


