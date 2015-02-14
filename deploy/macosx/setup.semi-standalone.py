import py2app
from setuptools import setup

# Build the .app file
setup(
    options=dict(
        py2app=dict(
            iconfile='resources/mapslicer.icns',
            excludes='wx,osgeo,PIL,numpy',
            semi_standalone='yes',
            use_pythonpath='yes',
            resources=['resources/license/LICENSE.txt','mapslicer'],
            plist=dict(
                CFBundleName               = "MapSlicer",
                CFBundleShortVersionString = "1.0.alpha2",     # must be in X.X.X format
                CFBundleGetInfoString      = "MapSlicer 1.0 alpha2",
                CFBundleExecutable         = "MapSlicer",
                CFBundleIdentifier         = "cz.klokan.mapslicer",
            ),
        ),
    ),
    app=[ 'mapslicer.py' ]
)
