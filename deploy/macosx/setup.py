import py2app
from setuptools import setup

# Build the .app file
setup(
    options=dict(
        py2app=dict(
            iconfile='resources/maptiler.icns',
            packages='wx',
            excludes='osgeo,PIL,numpy',
            #site_packages=True,
            #semi_standalone=True,
            resources=['resources/license/LICENSE.txt','maptiler'],
            plist=dict(
                CFBundleName               = "MapTiler",
                CFBundleShortVersionString = "1.0.alpha2",     # must be in X.X.X format
                CFBundleGetInfoString      = "MapTiler 1.0 alpha2",
                CFBundleExecutable         = "MapTiler",
                CFBundleIdentifier         = "cz.klokan.maptiler",
            ),
            frameworks=['PROJ.framework','GEOS.framework','SQLite3.framework','UnixImageIO.framework','GDAL.framework'],
        ),
    ),
    app=[ 'maptiler.py' ]
)
