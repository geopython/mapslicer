import py2app
from setuptools import setup

# Build the .app file
setup(
    options=dict(
        py2app=dict(
            iconfile='resources/maptiler.icns',
            excludes='wx,osgeo,PIL,numpy',
            semi_standalone='yes',
            use_pythonpath='yes',
            resources=['resources/license/LICENSE.txt','maptiler'],
            plist=dict(
                CFBundleName               = "MapTiler",
                CFBundleShortVersionString = "1.0.alpha2",     # must be in X.X.X format
                CFBundleGetInfoString      = "MapTiler 1.0 alpha2",
                CFBundleExecutable         = "MapTiler",
                CFBundleIdentifier         = "cz.klokan.maptiler",
            ),
        ),
    ),
    app=[ 'maptiler.py' ]
)
