#!/bin/sh
rm -Rf dist/MapSlicer.app/Contents/Frameworks/GDAL.framework/Versions/Current/libgdal.a
rm -Rf dist/MapSlicer.app/Contents/Frameworks/GDAL.framework/Versions/Current/Resources/doc
rm -Rf dist/MapSlicer.app/Contents/Frameworks/GDAL.framework/Versions/Current/Programs
rm -Rf dist/MapSlicer.app/Contents/Frameworks/PROJ.framework/Versions/Current/Programs
rm -Rf dist/MapSlicer.app/Contents/Frameworks/SQLite3.framework/Versions/Current/Programs
rm -Rf dist/MapSlicer.app/Contents/Frameworks/UnixImageIO.framework/Versions/Current/Programs

rm -Rf dist/MapSlicer.app/Contents/Resources/lib/python2.5/wx/tools

# Create versions for different architectures:
mkdir dist/i386
#ditto --rsrc --arch ppc dist/MapSlicer.app dist/MapSlicer-ppc.app
ditto --rsrc --arch i386 dist/MapSlicer.app dist/i386/MapSlicer.app
#lipo -thin i386 -output dist/i386/MapSlicer.app/binary... dist/MapSlicer.app/binary...
