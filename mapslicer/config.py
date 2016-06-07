#import gettext

version = "1.0 rc2"

profile = 'mercator'
files = []
nodata = None
srs = ""
customsrs = ""
srsformat = 0
tminz = 0
tmaxz = 0
format = False
resume = False
kml = False
outputdir = None
url = "http://" # TODO: Do not submit this to the command-line
viewer_google = False
viewer_openlayers = False
title = ""
copyright = "&copy;"
googlekey = ""
yahookey = ""

documentsdir = ""

bboxgeoref = False

# GetText
#_ = gettext.gettext
_ = lambda s: s

# WellKnownGeogCS
wellknowngeogcs = ['WGS84','WGS72','NAD27','NAD83']

# Subset of the GDAL supported file formats...
supportedfiles =  _("Supported raster files")+"|*.tif;*.tiff;*.kap;*.img;*.sid;*.ecw;*.jp2;*.j2k;*.nitf;*.h1;*.h2;*.hd;*.hdr;*.cit;*.rgb;*.raw;*.blx;*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.wms;*.vrt|" + \
	_("TIFF / BigTIFF / GeoTIFF (.tif)")+"|*.tif;*.tiff|" + \
	_("BSB Nautical Chart Format (.kap)")+"|*.kap|" + \
	_("JPEG2000 - JPEG 2000 (.jp2, .j2k)")+"|*.jp2;*.j2k|" + \
	_("MrSID - Multi-resolution Seamless Image Database (.sid)")+"|*.sid|" + \
	_("ECW - ERMapper Compressed Wavelets (.ecw)")+"|*.ecw|" + \
	_("HFA - Erdas Imagine Images (.img)")+"|*.img|" + \
	_("NITF - National Imagery Transmission Format (.nitf)")+"|*.nitf|" + \
	_("NDF - NLAPS Data Format (.h1,.h2,.hd)")+"|*.h1;*.h2;*.hd|" + \
	_("MFF - Vexcel MFF Raster (.hdr)")+"|*.hdr|" + \
	_("INGR - Intergraph Raster Format (.cit,.rgb,..)")+"|*.cit;*.rgb|" + \
	_("EIR - Erdas Imagine Raw (.raw)")+"|*.raw|" + \
	_("BLX - Magellan BLX Topo File Format (.blx)")+"|*.blx|" + \
	_("JPEG - Joint Photographic Experts Group JFIF (.jpg)")+"|*.jpg;*.jpeg|" + \
	_("PNG - Portable Network Graphics (.png)")+"|*.png|" + \
	_("GIF - Graphics Interchange Format (.gif)")+"|*.gif|" + \
	_("BMP - Microsoft Windows Device Independent Bitmap (.bmp)")+"|*.bmp|" + \
	_("WMS - GDAL driver for OGC Web Map Server (.wms)")+"|*.wms|" + \
	_("VRT - GDAL Virtual Raster (.vrt)")+"|*.vrt|" + \
	_("All files (*.*)")+"|*.*"

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
_('Custom definition of the system (WKT, Proj.4,..)'),
_('WGS84 - Latitude and longitude (geodetic)'),
_('Universal Transverse Mercator - UTM (projected)'),
_('Specify the id-number from the EPSG/ESRI database'),
_('Search the coordinate system by name'),
]

srsFormatListLocal = [
_('SRSCustom0'),_("SRSDefinition0"),
_('SRSCustom1'),_("SRSDefinition1"),
_('SRSCustom2'),_("SRSDefinition2"),
_('SRSCustom3'),_("SRSDefinition3"),
_('SRSCustom4'),_("SRSDefinition4"),
_('SRSCustom5'),_("SRSDefinition5"),
_('SRSCustom6'),_("SRSDefinition6"),
_('SRSCustom7'),_("SRSDefinition7"),
_('SRSCustom8'),_("SRSDefinition8"),
_('SRSCustom9'),_("SRSDefinition9")
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
datadir = wx.StandardPaths.Get().GetUserLocalDataDir()
if not os.path.isdir(datadir):
    os.mkdir(datadir)
f = wx.FileConfig(localFilename=os.path.join(datadir,'MapSlicer.cfg'))

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

