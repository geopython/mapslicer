import py2app
from setuptools import setup

# Build the .app file
setup(
    options=dict(
        py2app=dict(
            iconfile='resources/mapslicer.icns',
            packages='wx',
            excludes='osgeo,PIL,numpy',
            #site_packages=True,
            #semi_standalone=True,
            resources=['resources/license/LICENSE.txt','mapslicer'],
            plist=dict(
                CFBundleName               = "MapSlicer",
                CFBundleShortVersionString = "1.0.alpha2",     # must be in X.X.X format
                CFBundleGetInfoString      = "MapSlicer 1.0 alpha2",
                CFBundleExecutable         = "MapSlicer",
                CFBundleIdentifier         = "cz.klokan.mapslicer",
            ),
            frameworks=['PROJ.framework','GEOS.framework','SQLite3.framework','UnixImageIO.framework','GDAL.framework'],
        ),
    ),
    app=[ 'mapslicer.py' ]
)
