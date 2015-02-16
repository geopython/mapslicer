cd ../../..
rm -rf /usr/lib/mapslicer
rm /usr/share/applications/mapslicer.desktop
rm -rf /usr/share/mapslicer
rm -rf /usr/share/doc/mapslicer

mkdir -p /usr/lib/mapslicer
cp mapslicer.py /usr/lib/mapslicer/
cp -r mapslicer /usr/lib/mapslicer/

mkdir -p /usr/share/doc/mapslicer
cp README.txt /usr/share/doc/mapslicer/
cp deploy/linux/debian/copyright /usr/share/doc/mapslicer/
cp deploy/linux/mapslicer.desktop /usr/share/applications/
mkdir -p /usr/share/mapslicer
cp resources/icon.png /usr/share/mapslicer/

fpm -s dir -t deb -a all -n mapslicer -v 1.0.rc1 --description='Map Tile Generator for Mashups' -d python-gdal -d python-wxgtk2.8 -d python /usr/share/doc/mapslicer/ /usr/lib/mapslicer/ /usr/share/mapslicer/icon.png /usr/share/applications/mapslicer.desktop

