====================
MapSlicer Application
====================
https://wiki.osgeo.org/wiki/MapSlicer

MapSlicer is graphical application for online map publishing. Your map can create overlay of standard maps like Google Maps, Yahoo Maps, Microsoft VirtualEarth or OpenStreetMap and can be also visualized in 3D by Google Earth. Only thing you have to do for publishing the map is to upload the automatically generated directory with tiles into your webserver.

MapSlicer is an open-source application, distributed under New BSD License.
You can download the source code from repository at https://github.com/kalxas/mapslicer

It is running under Microsoft Windows, Apple Mac OS X as well as on UNIX systems like Linux Ubuntu.

Requirements
------------
In case you would like to run the application from the code you need:
- Python 2.5
- wxPython 2.8+
- GDAL 1.6+

Start of the application is done by running:

$ python mapslicer.py


Packaging
---------
The packaging scripts and instructions are in the directory /deploy/.


Development
-----------

Development of the project happens on GitHub. Pull Requests are welcome :)

We would like to thank Petr Pridal - Klokan for his contribution of the original MapTiler project.

