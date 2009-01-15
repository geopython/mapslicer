version = "1.0 alpha1"

profile = 'mercator'
files = []
nodata = None
srs = "EPSG:4326"
srsformat = 0
tminz = 0
tmaxz = 0
resume = False
kml = False
outputdir = ""
url = "http://" # TODO: Do not submit this to the command-line
viewer_google = False
viewer_openlayers = False
title = ""
copyright = "&copy;"
googlekey = ""
yahookey = ""

# Placeholder for GetText
def _(str):
	return str

# Subset of the GDAL supported file formats...
supportedfiles =  "Supported raster files|*.tif;*.tiff;*.kap;*.img;*.sid;*.ecw;*.jp2;*.j2k;*.nitf;*.h1;*.h2;*.hd;*.hdr;*.cit;*.rgb;*.raw;*.blx;*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.wms;*.vrt|" \
	"TIFF / BigTIFF / GeoTIFF (.tif)|*.tif;*.tiff|" \
	"BSB Nautical Chart Format (.kap)|*.kap|" \
	"JPEG2000 - JPEG 2000 (.jp2, .j2k)|*.jp2;*.j2k|" \
	"MrSID - Multi-resolution Seamless Image Database (.sid)|*.sid|" \
	"ECW - ERMapper Compressed Wavelets (.ecw)|*.ecw|" \
	"HFA - Erdas Imagine Images (.img)|*.img|" \
	"NITF - National Imagery Transmission Format (.nitf)|*.nitf|" \
	"NDF - NLAPS Data Format (.h1,.h2,.hd)|*.h1;*.h2;*.hd|" \
	"MFF - Vexcel MFF Raster (.hdr)|*.hdr|" \
	"INGR - Intergraph Raster Format (.cit,.rgb,..)|*.cit;*.rgb|" \
	"EIR -- Erdas Imagine Raw (.raw)|*.raw|" \
	"BLX -- Magellan BLX Topo File Format (.blx)|*.blx|" \
	"JPEG - Joint Photographic Experts Group JFIF (.jpg)|*.jpg;*.jpeg|" \
	"PNG - Portable Network Graphics (.png)|*.png|" \
	"GIF - Graphics Interchange Format (.gif)|*.gif|" \
	"BMP - Microsoft Windows Device Independent Bitmap (.bmp)|*.bmp|" \
	"WMS - GDAL driver for OGC Web Map Server (.wms)|*.wms|" \
	"VRT - GDAL Virtual Raster (.vrt)|*.vrt|" \
	"All files (*.*)|*.*"

srsFormatList = ['format automatically detected',
	'WKT - Well Known Text definition',
	'ESRI WKT - Well Known Text definition',
	'EPSG number',
	'EPSGA number',
	'Proj.4 definition'
]
