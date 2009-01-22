#!/bin/sh
rm -Rf dist/MapTiler.app/Contents/Frameworks/GDAL.framework/Versions/Current/libgdal.a
rm -Rf dist/MapTiler.app/Contents/Frameworks/GDAL.framework/Versions/Current/Resources/doc
rm -Rf dist/MapTiler.app/Contents/Frameworks/GDAL.framework/Versions/Current/Programs
rm -Rf dist/MapTiler.app/Contents/Frameworks/PROJ.framework/Versions/Current/Programs
rm -Rf dist/MapTiler.app/Contents/Frameworks/SQLite3.framework/Versions/Current/Programs
rm -Rf dist/MapTiler.app/Contents/Frameworks/UnixImageIO.framework/Versions/Current/Programs

rm -Rf dist/MapTiler.app/Contents/Resources/lib/python2.5/wx/tools

# Create versions for different architectures:
mkdir dist/i386
#ditto --rsrc --arch ppc dist/MapTiler.app dist/MapTiler-ppc.app
ditto --rsrc --arch i386 dist/MapTiler.app dist/i386/MapTiler.app
#lipo -thin i386 -output dist/i386/MapTiler.app/binary... dist/MapTiler.app/binary...
