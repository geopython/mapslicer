version = "1.0 alpha3"

profile = 'mercator'
files = []
nodata = None
srs = ""
customsrs = ""
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

documentsdir = ""

bboxgeoref = False


# Placeholder for GetText
def _(str):
	return str

# WellKnownGeogCS
wellknowngeogcs = ['WGS84','WGS72','NAD27','NAD83']

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

s = """
srsFormatList = ['format automatically detected',
        'WKT - Well Known Text definition',
        'ESRI WKT - Well Known Text definition',
        'EPSG number',
        'EPSGA number',
        'Proj.4 definition'
]
"""

srsFormatList = [
'Custom definition of the system (WKT, Proj.4,..)',
'WGS84 - Latitude and longitude (geodetic)',
'Universal Transverse Mercator - UTM (projected)',
'Specify the id-number from the EPSG/ESRI database',
'Search the coordinate system by name',
]

srsFormatListLocal = [
'SRSCustom0',"SRSDefinition0",
'SRSCustom1',"SRSDefinition1",
'SRSCustom2',"SRSDefinition2",
'SRSCustom3',"SRSDefinition3",
'SRSCustom4',"SRSDefinition4",
'SRSCustom5',"SRSDefinition5",
'SRSCustom6',"SRSDefinition6",
'SRSCustom7',"SRSDefinition7",
'SRSCustom8',"SRSDefinition8",
'SRSCustom9',"SRSDefinition9"
]

#English-speaking coordinate systems defaults:
# 'OSGB 1936 / British National Grid (projected)'
# 'NZMG - New Zealand Map Grid'
# ''

#French-speaking coordinate systems defaults:
# Lambert

#German-speaking coordinate systems defaults:
# ...

s = """
#A = wx.PySimpleApp()
#A.SetAppName(VENDOR_NAME)

datadir = wx.StandardPaths.Get().GetUserLocalDataDir()
if not os.path.isdir(datadir):
    os.mkdir(datadir)
f = wx.FileConfig(localFilename=os.path.join(datadir,'MapTiler.cfg'))

f.SetPath("APath")
print f.Read("Key")
f.Write("Key", "Value")
f.Flush()
"""

epsg4326 = """GEOGCS["WGS 84",
    DATUM["WGS_1984",
        SPHEROID["WGS 84",6378137,298.257223563,
            AUTHORITY["EPSG","7030"]],
        AUTHORITY["EPSG","6326"]],
    PRIMEM["Greenwich",0,
        AUTHORITY["EPSG","8901"]],
    UNIT["degree",0.01745329251994328,
        AUTHORITY["EPSG","9122"]],
    AUTHORITY["EPSG","4326"]]"""