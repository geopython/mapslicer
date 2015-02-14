import os, sys
from mapslicer import version

# py2exe - needs OSGeo4W with GDAL 1.6
if sys.platform in ['win32','win64']:
	from distutils.core import setup
	import glob
	import py2exe

	sys.path.insert(0, 'C:\\OSGeo4W\\apps\\gdal-16\\pymod' )
	os.environ['PATH'] += ';C:\\OSGeo4W\\bin'

	setup(name='MapSlicer',
	      version=version.replace(' ','.'),
	      description = "MapSlicer - Map Tile Generator for Mashups",
	      long_description= "MapSlicer is a powerful tool for online map publishing and generation of map overlay mashups. Your geodata are transformed to the tiles compatible with Google Maps and Earth - ready for uploading to your webserver.",
	      url='https://github.com/kalxas/mapslicer',
	      author='Klokan Petr Pridal',
	      author_email='klokan@klokan.cz',
	      packages=['mapslicer'],
	      scripts=['mapslicer.py'],
	      windows=[ {'script':'mapslicer.py', "icon_resources": [(1, os.path.join('resources', 'mapslicer.ico'))] } ],
	      data_files=[
	        ('proj', glob.glob('C:\\OSGeo4W\\share\\proj\\*')),
	        ('gdal', glob.glob('C:\\OSGeo4W\\apps\\gdal-16\\share\\gdal\\*')),
	        ('gdalplugins', glob.glob('C:\\OSGeo4W\\apps\\gdal-16\\bin\\gdalplugins\\*.*')),
	        ('', glob.glob('C:\\OSGeo4W\\bin\\*.dll')+glob.glob('C:\\OSGeo4W\\bin\\*.manifest')),
	      ],
	      options={'py2exe':{'packages':['mapslicer'],
	                         'includes':['encodings','osgeo'],
	                         'excludes':['PIL','numpy','wx.BitmapFromImage','wx.EmptyIcon']
	                         },
	               },

	)

# py2app - creates 'fat' standalone Universal binary - with size around 160MB :-(
# Use 'Build Applet.app' for small Leopard-only bundle with dependency on the Kyngchaos GDAL 1.6 Framework
if sys.platform == 'darwin':
	from setuptools import setup
	import py2app

	# Build the .app file
	setup(
	    options=dict(
	        py2app=dict(
	            iconfile='resources/mapslicer.icns',
	            packages='wx',
	            excludes='osgeo,PIL,numpy',
	            resources=['resources/license/LICENSE.txt','mapslicer'],
	            plist=dict(
	                CFBundleName               = "MapSlicer",
	                CFBundleShortVersionString = version.replace(' ','.'),
	                CFBundleGetInfoString      = "MapSlicer %s" % version,
	                CFBundleExecutable         = "MapSlicer",
	                CFBundleIdentifier         = "cz.klokan.mapslicer",
	            ),
	            frameworks=['PROJ.framework','GEOS.framework','SQLite3.framework','UnixImageIO.framework','GDAL.framework'],
	        ),
	    ),
	    app=[ 'mapslicer.py' ]
	)
