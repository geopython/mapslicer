import os, sys
from maptiler import version

# py2exe - needs OSGeo4W with GDAL 1.6
if sys.platform in ['win32','win64']:
	from distutils.core import setup
	import glob
	import py2exe

	sys.path.insert(0, 'C:\\OSGeo4W\\apps\\gdal-16\\pymod' )
	os.environ['PATH'] += ';C:\\OSGeo4W\\bin'

	setup(name='MapTiler',
	      version=version.replace(' ','.'),
	      description = "MapTiler - Map Tile Generator for Mashups",
	      long_description= "MapTiler is a powerful tool for online map publishing and generation of map overlay mashups. Your geodata are transformed to the tiles compatible with Google Maps and Earth - ready for uploading to your webserver.",
	      url='http://www.maptiler.org/',
	      author='Klokan Petr Pridal',
	      author_email='klokan@klokan.cz',
	      packages=['maptiler'],
	      scripts=['maptiler.py'],
	      windows=[ {'script':'maptiler.py', "icon_resources": [(1, os.path.join('resources', 'maptiler.ico'))] } ],
	      data_files=[
	        ('proj', glob.glob('C:\\OSGeo4W\\share\\proj\\*')),
	        ('gdal', glob.glob('C:\\OSGeo4W\\apps\\gdal-16\\share\\gdal\\*')),
	        ('gdalplugins', glob.glob('C:\\OSGeo4W\\apps\\gdal-16\\bin\\gdalplugins\\*.*')),
	        ('', glob.glob('C:\\OSGeo4W\\bin\\*.dll')+glob.glob('C:\\OSGeo4W\\bin\\*.manifest')),
	      ],
	      options={'py2exe':{'packages':['maptiler'],
	                         'includes':['encodings','osgeo'],
	                         'excludes':['PIL','numpy','wx.BitmapFromImage','wx.EmptyIcon']
	                         },
	               },

	)

# py2app - semi-standalone binary for Leopard-only with dependency on the Kyngchaos GDAL 1.6 Framework
# if you need Universal binary ('fat' - around 160 MB) then check deploy/macosx/setup.py
if sys.platform == 'darwin':
	from setuptools import setup
	import py2app

	# Build the .app file
	setup(
	    options=dict(
	        py2app=dict(
	            iconfile='resources/maptiler.icns',
	            excludes='wx,osgeo,PIL,numpy',
	            semi_standalone=True,
	            use_pythonpath=True,
	            resources=['resources/license/LICENSE.txt','maptiler'],
	            plist=dict(
	                CFBundleName               = "MapTiler",
	                CFBundleShortVersionString = version.replace(' ','.'),     # must be in X.X.X format
	                CFBundleGetInfoString      = "MapTiler %s" % version,
	                CFBundleExecutable         = "MapTiler",
	                CFBundleIdentifier         = "cz.klokan.maptiler",
	            ),
	        ),
	    ),
	    app=[ 'maptiler.py' ]
	)
