#!/usr/bin/env python
#******************************************************************************
#  $Id: gdal2tiles.py 15748 2008-11-17 16:30:54Z klokan $
# 
# Project:  Google Summer of Code 2007, 2008 (http://code.google.com/soc/)
# Support:  BRGM (http://www.brgm.fr)
# Purpose:  Convert a raster into TMS (Tile Map Service) tiles in a directory.
#           - generate Google Earth metadata (KML SuperOverlay)
#           - generate simple HTML viewer based on Google Maps and OpenLayers
#           - support of global tiles (Spherical Mercator) for compatibility
#               with interactive web maps a la Google Maps
# Author:   Klokan Petr Pridal, klokan at klokan dot cz
# Web:      http://www.klokan.cz/projects/gdal2tiles/
# GUI:      https://github.com/kalxas/mapslicer
#
###############################################################################
# Copyright (c) 2008, Klokan Petr Pridal
# 
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
# 
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
# 
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
#******************************************************************************

from osgeo import gdal
from osgeo import osr

import sys
import os
import math

from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

try:
	from PIL import Image
	import numpy
	import osgeo.gdal_array as gdalarray
except:
	# 'antialias' resampling is not available
	pass

__version__ = "$Id: gdal2tiles.py 15748 2008-11-17 16:30:54Z klokan $"

resampling_list = ('average','near','bilinear','cubic','cubicspline','lanczos','antialias')
tile_formats_list = ('png', 'jpeg', 'hybrid')
profile_list = ('mercator','geodetic','raster','gearth','garmin') #,'zoomify')
webviewer_list = ('all','google','openlayers','none')

format_extension = {
	"PNG" : "png",
	"JPEG" : "jpg"
}

format_mime = {
	"PNG" : "image/png",
	"JPEG" : "image/jpeg"
}

jpeg_quality = 85
jpeg_gdal_options = ["QUALITY=%d" % jpeg_quality]

# =============================================================================
# =============================================================================
# =============================================================================

__doc__globalmaptiles = """
globalmaptiles.py

Global Map Tiles as defined in Tile Map Service (TMS) Profiles
==============================================================

Functions necessary for generation of global tiles used on the web.
It contains classes implementing coordinate conversions for:

  - GlobalMercator (based on EPSG:900913 = EPSG:3785)
       for Google Maps, Yahoo Maps, Microsoft Maps compatible tiles
  - GlobalGeodetic (based on EPSG:4326)
       for OpenLayers Base Map and Google Earth compatible tiles

More info at:

http://wiki.osgeo.org/wiki/Tile_Map_Service_Specification
http://wiki.osgeo.org/wiki/WMS_Tiling_Client_Recommendation
http://msdn.microsoft.com/en-us/library/bb259689.aspx
http://code.google.com/apis/maps/documentation/overlays.html#Google_Maps_Coordinates

Originally created by Klokan Petr Pridal on 2008-07-03.
Google Summer of Code 2008, project GDAL2Tiles for OSGEO.

Class is available under the open-source GDAL license (www.gdal.org).
"""

import math

MAXZOOMLEVEL = 32

class GlobalMercator(object):
	"""
	TMS Global Mercator Profile
	---------------------------

	Functions necessary for generation of tiles in Spherical Mercator projection,
	EPSG:900913 (EPSG:gOOglE, Google Maps Global Mercator), EPSG:3785, OSGEO:41001.

	Such tiles are compatible with Google Maps, Microsoft Virtual Earth, Yahoo Maps,
	UK Ordnance Survey OpenSpace API, ...
	and you can overlay them on top of base maps of those web mapping applications.
	
	Pixel and tile coordinates are in TMS notation (origin [0,0] in bottom-left).

	What coordinate conversions do we need for TMS Global Mercator tiles::

	     LatLon      <->       Meters      <->     Pixels    <->       Tile     

	 WGS84 coordinates   Spherical Mercator  Pixels in pyramid  Tiles in pyramid
	     lat/lon            XY in metres     XY pixels Z zoom      XYZ from TMS 
	    EPSG:4326           EPSG:900913                                         
	     .----.              ---------               --                TMS      
	    /      \     <->     |       |     <->     /----/    <->      Google    
	    \      /             |       |           /--------/          QuadTree   
	     -----               ---------         /------------/                   
	   KML, public         WebMapService         Web Clients      TileMapService

	What is the coordinate extent of Earth in EPSG:900913?

	  [-20037508.342789244, -20037508.342789244, 20037508.342789244, 20037508.342789244]
	  Constant 20037508.342789244 comes from the circumference of the Earth in meters,
	  which is 40 thousand kilometers, the coordinate origin is in the middle of extent.
      In fact you can calculate the constant as: 2 * math.pi * 6378137 / 2.0
	  $ echo 180 85 | gdaltransform -s_srs EPSG:4326 -t_srs EPSG:900913
	  Polar areas with abs(latitude) bigger then 85.05112878 are clipped off.

	What are zoom level constants (pixels/meter) for pyramid with EPSG:900913?

	  whole region is on top of pyramid (zoom=0) covered by 256x256 pixels tile,
	  every lower zoom level resolution is always divided by two
	  initialResolution = 20037508.342789244 * 2 / 256 = 156543.03392804062

	What is the difference between TMS and Google Maps/QuadTree tile name convention?

	  The tile raster itself is the same (equal extent, projection, pixel size),
	  there is just different identification of the same raster tile.
	  Tiles in TMS are counted from [0,0] in the bottom-left corner, id is XYZ.
	  Google placed the origin [0,0] to the top-left corner, reference is XYZ.
	  Microsoft is referencing tiles by a QuadTree name, defined on the website:
	  http://msdn2.microsoft.com/en-us/library/bb259689.aspx

	The lat/lon coordinates are using WGS84 datum, yeh?

	  Yes, all lat/lon we are mentioning should use WGS84 Geodetic Datum.
	  Well, the web clients like Google Maps are projecting those coordinates by
	  Spherical Mercator, so in fact lat/lon coordinates on sphere are treated as if
	  the were on the WGS84 ellipsoid.
	 
	  From MSDN documentation:
	  To simplify the calculations, we use the spherical form of projection, not
	  the ellipsoidal form. Since the projection is used only for map display,
	  and not for displaying numeric coordinates, we don't need the extra precision
	  of an ellipsoidal projection. The spherical projection causes approximately
	  0.33 percent scale distortion in the Y direction, which is not visually noticable.

	How do I create a raster in EPSG:900913 and convert coordinates with PROJ.4?

	  You can use standard GIS tools like gdalwarp, cs2cs or gdaltransform.
	  All of the tools supports -t_srs 'epsg:900913'.

	  For other GIS programs check the exact definition of the projection:
	  More info at http://spatialreference.org/ref/user/google-projection/
	  The same projection is degined as EPSG:3785. WKT definition is in the official
	  EPSG database.

	  Proj4 Text:
	    +proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0
	    +k=1.0 +units=m +nadgrids=@null +no_defs

	  Human readable WKT format of EPGS:900913:
	     PROJCS["Google Maps Global Mercator",
	         GEOGCS["WGS 84",
	             DATUM["WGS_1984",
	                 SPHEROID["WGS 84",6378137,298.2572235630016,
	                     AUTHORITY["EPSG","7030"]],
	                 AUTHORITY["EPSG","6326"]],
	             PRIMEM["Greenwich",0],
	             UNIT["degree",0.0174532925199433],
	             AUTHORITY["EPSG","4326"]],
	         PROJECTION["Mercator_1SP"],
	         PARAMETER["central_meridian",0],
	         PARAMETER["scale_factor",1],
	         PARAMETER["false_easting",0],
	         PARAMETER["false_northing",0],
	         UNIT["metre",1,
	             AUTHORITY["EPSG","9001"]]]
	"""

	def __init__(self, tileSize=256):
		"Initialize the TMS Global Mercator pyramid"
		self.tileSize = tileSize
		self.initialResolution = 2 * math.pi * 6378137 / self.tileSize
		# 156543.03392804062 for tileSize 256 pixels
		self.originShift = 2 * math.pi * 6378137 / 2.0
		# 20037508.342789244

	def LatLonToMeters(self, lat, lon ):
		"Converts given lat/lon in WGS84 Datum to XY in Spherical Mercator EPSG:900913"

		mx = lon * self.originShift / 180.0
		my = math.log( math.tan((90 + lat) * math.pi / 360.0 )) / (math.pi / 180.0)

		my = my * self.originShift / 180.0
		return mx, my

	def MetersToLatLon(self, mx, my ):
		"Converts XY point from Spherical Mercator EPSG:900913 to lat/lon in WGS84 Datum"

		lon = (mx / self.originShift) * 180.0
		lat = (my / self.originShift) * 180.0

		lat = 180 / math.pi * (2 * math.atan( math.exp( lat * math.pi / 180.0)) - math.pi / 2.0)
		return lat, lon

	def PixelsToMeters(self, px, py, zoom):
		"Converts pixel coordinates in given zoom level of pyramid to EPSG:900913"

		res = self.Resolution( zoom )
		mx = px * res - self.originShift
		my = py * res - self.originShift
		return mx, my
		
	def MetersToPixels(self, mx, my, zoom):
		"Converts EPSG:900913 to pyramid pixel coordinates in given zoom level"
				
		res = self.Resolution( zoom )
		px = (mx + self.originShift) / res
		py = (my + self.originShift) / res
		return px, py
	
	def PixelsToTile(self, px, py):
		"Returns a tile covering region in given pixel coordinates"

		tx = int( math.ceil( px / float(self.tileSize) ) - 1 )
		ty = int( math.ceil( py / float(self.tileSize) ) - 1 )
		return tx, ty

	def PixelsToRaster(self, px, py, zoom):
		"Move the origin of pixel coordinates to top-left corner"
		
		mapSize = self.tileSize << zoom
		return px, mapSize - py
		
	def MetersToTile(self, mx, my, zoom):
		"Returns tile for given mercator coordinates"
		
		px, py = self.MetersToPixels( mx, my, zoom)
		return self.PixelsToTile( px, py)

	def TileBounds(self, tx, ty, zoom):
		"Returns bounds of the given tile in EPSG:900913 coordinates"
		
		minx, miny = self.PixelsToMeters( tx*self.tileSize, ty*self.tileSize, zoom )
		maxx, maxy = self.PixelsToMeters( (tx+1)*self.tileSize, (ty+1)*self.tileSize, zoom )
		return ( minx, miny, maxx, maxy )

	def TileLatLonBounds(self, tx, ty, zoom ):
		"Returns bounds of the given tile in latutude/longitude using WGS84 datum"

		bounds = self.TileBounds( tx, ty, zoom)
		minLat, minLon = self.MetersToLatLon(bounds[0], bounds[1])
		maxLat, maxLon = self.MetersToLatLon(bounds[2], bounds[3])
		 
		return ( minLat, minLon, maxLat, maxLon )
		
	def Resolution(self, zoom ):
		"Resolution (meters/pixel) for given zoom level (measured at Equator)"
		
		# return (2 * math.pi * 6378137) / (self.tileSize * 2**zoom)
		return self.initialResolution / (2**zoom)
		
	def ZoomForPixelSize(self, pixelSize ):
		"Maximal scaledown zoom of the pyramid closest to the pixelSize."
		
		for i in range(MAXZOOMLEVEL):
			if pixelSize > self.Resolution(i):
				if i!=0:
					return i-1
				else:
					return 0 # We don't want to scale up
		
	def GoogleTile(self, tx, ty, zoom):
		"Converts TMS tile coordinates to Google Tile coordinates"
		
		# coordinate origin is moved from bottom-left to top-left corner of the extent
		return tx, (2**zoom - 1) - ty

	def QuadTree(self, tx, ty, zoom ):
		"Converts TMS tile coordinates to Microsoft QuadTree"
		
		quadKey = ""
		ty = (2**zoom - 1) - ty
		for i in range(zoom, 0, -1):
			digit = 0
			mask = 1 << (i-1)
			if (tx & mask) != 0:
				digit += 1
			if (ty & mask) != 0:
				digit += 2
			quadKey += str(digit)
			
		return quadKey

#---------------------

class GlobalGeodetic(object):
	"""
	TMS Global Geodetic Profile
	---------------------------

	Functions necessary for generation of global tiles in Plate Carre projection,
	EPSG:4326, "unprojected profile".

	Such tiles are compatible with Google Earth (as any other EPSG:4326 rasters)
	and you can overlay the tiles on top of OpenLayers base map.
	
	Pixel and tile coordinates are in TMS notation (origin [0,0] in bottom-left).

	What coordinate conversions do we need for TMS Global Geodetic tiles?

	  Global Geodetic tiles are using geodetic coordinates (latitude,longitude)
	  directly as planar coordinates XY (it is also called Unprojected or Plate
	  Carree). We need only scaling to pixel pyramid and cutting to tiles.
	  Pyramid has on top level two tiles, so it is not square but rectangle.
	  Area [-180,-90,180,90] is scaled to 512x256 pixels.
	  TMS has coordinate origin (for pixels and tiles) in bottom-left corner.
	  Rasters are in EPSG:4326 and therefore are compatible with Google Earth.

	     LatLon      <->      Pixels      <->     Tiles     

	 WGS84 coordinates   Pixels in pyramid  Tiles in pyramid
	     lat/lon         XY pixels Z zoom      XYZ from TMS 
	    EPSG:4326                                           
	     .----.                ----                         
	    /      \     <->    /--------/    <->      TMS      
	    \      /         /--------------/                   
	     -----        /--------------------/                
	   WMS, KML    Web Clients, Google Earth  TileMapService
	"""

	def __init__(self, tileSize = 256):
		self.tileSize = tileSize

	def LatLonToPixels(self, lat, lon, zoom):
		"Converts lat/lon to pixel coordinates in given zoom of the EPSG:4326 pyramid"

		res = 180.0 / self.tileSize / 2**zoom
		px = (180 + lat) / res
		py = (90 + lon) / res
		return px, py

	def PixelsToTile(self, px, py):
		"Returns coordinates of the tile covering region in pixel coordinates"

		tx = int( math.ceil( px / float(self.tileSize) ) - 1 )
		ty = int( math.ceil( py / float(self.tileSize) ) - 1 )
		return tx, ty
	
	def LatLonToTile(self, lat, lon, zoom):
		"Returns the tile for zoom which covers given lat/lon coordinates"
		
		px, py = self.LatLonToPixels( lat, lon, zoom)
		return self.PixelsToTile(px,py)

	def Resolution(self, zoom ):
		"Resolution (arc/pixel) for given zoom level (measured at Equator)"
		
		return 180.0 / self.tileSize / 2**zoom
		#return 180 / float( 1 << (8+zoom) )
		
	def ZoomForPixelSize(self, pixelSize ):
		"Maximal scaledown zoom of the pyramid closest to the pixelSize."

		for i in range(MAXZOOMLEVEL):
			if pixelSize > self.Resolution(i):
				if i!=0:
					return i-1
				else:
					return 0 # We don't want to scale up

	def TileBounds(self, tx, ty, zoom):
		"Returns bounds of the given tile"
		res = 180.0 / self.tileSize / 2**zoom
		return (
			tx*self.tileSize*res - 180,
			ty*self.tileSize*res - 90,
			(tx+1)*self.tileSize*res - 180,
			(ty+1)*self.tileSize*res - 90
		)
		
	def TileLatLonBounds(self, tx, ty, zoom):
		"Returns bounds of the given tile in the SWNE form"
		b = self.TileBounds(tx, ty, zoom)
		return (b[1],b[0],b[3],b[2])

#---------------------
# TODO: Finish Zoomify implementation!!!
class Zoomify(object):
	"""
	Tiles compatible with the Zoomify viewer
	----------------------------------------
	"""

	def __init__(self, width, height, tilesize = 256, tileformat='jpg'):
		"""Initialization of the Zoomify tile tree"""
		
		self.tilesize = tilesize
		self.tileformat = tileformat
		imagesize = (width, height)
		tiles = ( math.ceil( width / tilesize ), math.ceil( height / tilesize ) )

		# Size (in tiles) for each tier of pyramid.
		self.tierSizeInTiles = []
		self.tierSizeInTiles.push( tiles )

		# Image size in pixels for each pyramid tierself
		self.tierImageSize = []
		self.tierImageSize.append( imagesize );

		while (imagesize[0] > tilesize or imageSize[1] > tilesize ):
			imagesize = (math.floor( imagesize[0] / 2 ), math.floor( imagesize[1] / 2) )
			tiles = ( math.ceil( imagesize[0] / tilesize ), math.ceil( imagesize[1] / tilesize ) )
			self.tierSizeInTiles.append( tiles )
			self.tierImageSize.append( imagesize )

		self.tierSizeInTiles.reverse()
		self.tierImageSize.reverse()
	
		# Depth of the Zoomify pyramid, number of tiers (zoom levels)
		self.numberOfTiers = len(self.tierSizeInTiles)
											
		# Number of tiles up to the given tier of pyramid.
		self.tileCountUpToTier = []
		self.tileCountUpToTier[0] = 0
		for i in range(1, self.numberOfTiers+1):
			self.tileCountUpToTier.append(
				self.tierSizeInTiles[i-1][0] * self.tierSizeInTiles[i-1][1] + self.tileCountUpToTier[i-1]
			)		
	
	def tilefilename(self, x, y, z):
		"""Returns filename for tile with given coordinates"""
		
		tileIndex = x + y * self.tierSizeInTiles[z][0] + self.tileCountUpToTier[z]
		return os.path.join("TileGroup%.0f" % math.floor( tileIndex / 256 ),
			"%s-%s-%s.%s" % ( z, x, y, self.tileformat))

# =============================================================================
# =============================================================================
# =============================================================================


class GDAL2Tiles(object):

	# -------------------------------------------------------------------------
	def process(self):
		"""The main processing function, runs all the main steps of processing"""
		
		# Opening and preprocessing of the input file
		self.open_input()

		# Generation of main metadata files and HTML viewers
		self.generate_metadata()
		
		# Generation of the lowest tiles
		self.generate_base_tiles()
		
		# Generation of the overview tiles (higher in the pyramid)
		self.generate_overview_tiles()

		# Generating of KML
		self.generate_kml()

	# -------------------------------------------------------------------------
	def error(self, msg, details = "" ):
		"""Print an error message and stop the processing"""

		if details is not None:
			msg += "\n\n" + details

		if not self.is_subprocess:
			self.parser.error(msg)
		else:
			raise Exception(msg)

	# -------------------------------------------------------------------------
	def progressbar(self, complete = 0.0):
		"""Print progressbar for float value 0..1"""
		
		if self.is_subprocess:
			sys.stderr.write("%f\n" % complete)
			sys.stderr.flush()
		else:
			gdal.TermProgress_nocb(complete)

	# -------------------------------------------------------------------------
	def stop(self):
		"""Stop the rendering immediately"""
		self.stopped = True

	# -------------------------------------------------------------------------
	def __init__(self, arguments, is_subprocess=False, gdalcache=None):
		"""Constructor function - initialization"""
		
		self.stopped = False
		self.input = None
		self.output = None

		self.is_subprocess = is_subprocess

		# Should we read bigger window of the input raster and scale it down?
		# Note: Modified leter by open_input()
		# Not for 'near' resampling
		# Not for Wavelet based drivers (JPEG2000, ECW, MrSID)
		# Not for 'raster' profile
		self.scaledquery = True

		# Should we use Read on the input file for generating overview tiles?
		# Note: Modified later by open_input()
		# Otherwise the overview tiles are generated from existing underlying tiles
		self.overviewquery = False
		
		# RUN THE ARGUMENT PARSER:
		
		self.optparse_init()
		self.options, self.args = self.parser.parse_args(args=arguments)
		if not self.args:
			self.error("No input file specified")

		# POSTPROCESSING OF PARSED ARGUMENTS:

		# Tile size 
		try:
			self.tilesize = int(self.options.tilesize)
		except:
			self.tilesize = 256
			if self.options.profile == 'garmin':
				self.tilesize = 512

		# How big should be query window be for scaling down
		# Later on reset according the chosen resampling algorightm
		self.querysize = 4 * self.tilesize

		# Workaround for old versions of GDAL
		try:
			if (self.options.verbose and self.options.resampling == 'near') or gdal.TermProgress_nocb:
				pass
		except:
			self.error("This version of GDAL is not supported. Please upgrade to 1.6+.")
			#,"You can try run crippled version of gdal2tiles with parameters: -v -r 'near'")
		
		# Is output directory the last argument?

		# Test output directory, if it doesn't exist
		if os.path.isdir(self.args[-1]) or ( len(self.args) > 1 and not os.path.exists(self.args[-1])):
			self.output = self.args[-1]
			self.args = self.args[:-1]

		# More files on the input not directly supported yet
		
		if (len(self.args) > 1):
			self.error("Processing of several input files is not supported.",
			"""Please first use a tool like gdal_vrtmerge.py or gdal_merge.py on the files:
gdal_vrtmerge.py -o merged.vrt %s""" % " ".join(self.args))
			# TODO: Call functions from gdal_vrtmerge.py directly
			
		self.input = self.args[0]
		
		# Default values for not given options
		
		if not self.output:
			# Directory with input filename without extension in actual directory
			self.output = os.path.splitext(os.path.basename( self.input ))[0]
				
		if not self.options.title:
			self.options.title = os.path.basename( self.input )

		if self.options.url and not self.options.url.endswith('/'):
			self.options.url += '/'
		if self.options.url:
			self.options.url += os.path.basename( self.output ) + '/'

		# Supported options
		
		if self.options.resampling == 'average':
			try:
				if gdal.RegenerateOverview:
					pass
			except:
				self.error("'average' resampling algorithm is not available.", "Please use -r 'near' argument or upgrade to newer version of GDAL.")
		
		elif self.options.resampling == 'antialias':
			try:
				if numpy:
					pass
			except:
				self.error("'antialias' resampling algorithm is not available.", "Install PIL (Python Imaging Library) and numpy.")
		
		elif self.options.resampling == 'near':
			self.querysize = self.tilesize
		elif self.options.resampling == 'bilinear':
			self.querysize = self.tilesize * 2

		# Tile format.
		if self.options.tile_format is None:
			if self.options.profile == 'gearth':
				self.options.tile_format = 'hybrid'
			elif self.options.profile == 'garmin':
				self.options.tile_format = 'jpeg'
			else:
				self.options.tile_format = 'png'
				
		# Tile size and no webviewer for garmin profile
		if self.options.profile == 'garmin':
			self.options.webviewer = 'none'
			self.options.url = ''

		# Webviewer default depends on tile format.
		if self.options.webviewer is None:
			if self.options.tile_format == 'hybrid':
				self.options.webviewer = 'none'
			else:
				self.options.webviewer = 'all'
		# We don't support webviewers with hybrid trees yet.
		elif self.options.tile_format == 'hybrid' and self.options.webviewer != 'none':
			print ("WARNING: hybrid tile format is incompatible with webviewers you selected (%s), " +
				   "so they will not be created.") % self.options.webviewer
			self.options.webviewer = "none"

		# User specified zoom levels
		self.tminz = None
		self.tmaxz = None
		if self.options.zoom:
			minmax = self.options.zoom.split('-',1)
			minmax.extend([''])
			min, max = minmax[:2]
			self.tminz = int(min)
			if max:
				self.tmaxz = int(max)
			else:
				self.tmaxz = int(min) 
		
		# KML generation
		self.kml = self.options.kml
		if self.options.kml_depth is not None:
			self.kml_depth = int(self.options.kml_depth)
			assert self.kml_depth > 0
		else:
			if self.options.profile == 'gearth':
				self.kml_depth = 3
			else:
				self.kml_depth = 1

		if self.options.kmz is None:
			self.options.kmz = self.options.profile == 'gearth'

		# GDAL Cache
		if gdalcache is not None: # default gdal.GetCacheMax() == 40*1024*1024:
			gdal.SetCacheMax(gdalcache)

		# Output the results

		if self.options.verbose:
			print "Options:", self.options
			print "Input:", self.input
			print "Output:", self.output
			print "Cache: %s MB" % (gdal.GetCacheMax() / 1024 / 1024)
			print

	# -------------------------------------------------------------------------
	def optparse_init(self):
		"""Prepare the option parser for input (argv)"""
		
		from optparse import OptionParser, OptionGroup
		usage = "Usage: %prog [options] input_file(s) [output]"
		p = OptionParser(usage, version="%prog "+ __version__)
		p.add_option("-p", "--profile", dest='profile', type='choice', choices=profile_list,
						  help="Tile cutting profile (%s) - default 'mercator' (Google Maps compatible)" % ",".join(profile_list))
		p.add_option("-r", "--resampling", dest="resampling", type='choice', choices=resampling_list,
						help="Resampling method (%s) - default 'average'" % ",".join(resampling_list))
		p.add_option("-f", "--tile-format", dest="tile_format", type='choice', choices=tile_formats_list,
						help="Image format of generated tiles (%s) - default 'png'" % ",".join(tile_formats_list))
		p.add_option('-s', '--s_srs', dest="s_srs", metavar="SRS",
						  help="The spatial reference system used for the source input data")
		p.add_option('-z', '--zoom', dest="zoom",
						  help="Zoom levels to render (format:'2-5' or '10').")
		p.add_option('-e', '--resume', dest="resume", action="store_true",
						  help="Resume mode. Generate only missing files.")
		p.add_option('-a', '--srcnodata', dest="srcnodata", metavar="NODATA",
						  help="NODATA transparency value to assign to the input data")
		p.add_option('-i', '--init-dest', dest="init_dest",
						  help="Colour used to initialize output, only for 'jpeg' tile format")
		p.add_option('', '--tilesize', dest="tilesize",
						  help="Size of the tiles - default 256")
		p.add_option("-v", "--verbose",
						  action="store_true", dest="verbose",
						  help="Print status messages to stdout")

		# KML options 
		g = OptionGroup(p, "KML (Google Earth) options", "Options for generated Google Earth SuperOverlay metadata")
		g.add_option("-k", "--force-kml", dest='kml', action="store_true",
						  help="Generate KML for Google Earth - default for 'geodetic' profile and 'raster' in EPSG:4326. For a dataset with different projection use with caution!")
		g.add_option("-n", "--no-kml", dest='kml', action="store_false",
						  help="Avoid automatic generation of KML files for EPSG:4326")
		g.add_option("-u", "--url", dest='url',
						  help="URL address where the generated tiles are going to be published")
		g.add_option('-d', '--kml-depth', dest="kml_depth",
						  help="How many levels to store before linking, default 1")
		g.add_option('--kmz', dest="kmz", action="store_true",
						  help="Compress KML files into KMZ format, default for 'gearth' profile")
		g.add_option('--no-kmz', dest="kmz", action="store_false",
						  help="Do not compress KML files into KMZ format, default for 'mercator', 'geodetic' and 'raster' profiles")
		p.add_option_group(g)

		# HTML options
		g = OptionGroup(p, "Web viewer options", "Options for generated HTML viewers a la Google Maps")
		g.add_option("-w", "--webviewer", dest='webviewer', type='choice', choices=webviewer_list,
						  help="Web viewer to generate (%s) - default 'all'" % ",".join(webviewer_list))
		g.add_option("-t", "--title", dest='title',
						  help="Title of the map")
		g.add_option("-c", "--copyright", dest='copyright',
						  help="Copyright for the map")
		g.add_option("-g", "--googlekey", dest='googlekey',
						  help="Google Maps API key from http://code.google.com/apis/maps/signup.html")
		g.add_option("-y", "--yahookey", dest='yahookey',
						  help="Yahoo Application ID from http://developer.yahoo.com/wsregapp/")
		p.add_option_group(g)
		
		# TODO: MapFile + TileIndexes per zoom level for efficient MapServer WMS
		#g = OptionGroup(p, "WMS MapServer metadata", "Options for generated mapfile and tileindexes for MapServer")
		#g.add_option("-i", "--tileindex", dest='wms', action="store_true"
		#				  help="Generate tileindex and mapfile for MapServer (WMS)")
		# p.add_option_group(g)

		p.set_defaults(verbose=False, profile="mercator", kml=False, url=None,
		copyright='', resampling='average', resume=False, tilesize=None,
		googlekey='INSERT_YOUR_KEY_HERE', yahookey='INSERT_YOUR_YAHOO_APP_ID_HERE')

		self.parser = p
		



	# -------------------------------------------------------------------------
	def open_input(self):
		"""Initialization of the input raster, reprojection if necessary"""
		
		gdal.SetConfigOption("GDAL_PAM_ENABLED", "YES")
		gdal.AllRegister()

		# Open the input file
		if self.input:
			self.in_ds = gdal.Open(self.input, gdal.GA_ReadOnly)
		else:
			raise Exception("No input file was specified")

		if self.options.verbose:
			print "Input file:", "( %sP x %sL - %s bands)" % (self.in_ds.RasterXSize, self.in_ds.RasterYSize, self.in_ds.RasterCount)

		if not self.in_ds:
			# Note: GDAL prints the ERROR message too
			self.error("It is not possible to open the input file '%s'." % self.input )
			
		# Read metadata from the input file
		if self.in_ds.RasterCount == 0:
			self.error( "Input file '%s' has no raster band" % self.input )
			
		if self.in_ds.GetRasterBand(1).GetRasterColorTable():
			# TODO: Process directly paletted dataset by generating VRT in memory
			self.error( "Please convert this file to RGB/RGBA and run gdal2tiles on the result.",
			"""From paletted file you can create RGBA file (temp.vrt) by:
gdal_translate -of vrt -expand rgba %s temp.vrt
then run:
gdal2tiles temp.vrt""" % self.input )

		# Get NODATA value
		# User supplied values overwrite everything else.
		if self.options.srcnodata is not None:
			nds = map(float, self.options.srcnodata.split(','))
			if len(nds) < self.in_ds.RasterCount:
				self.in_nodata = (nds * self.in_ds.RasterCount)[:self.in_ds.RasterCount]
			else:
				self.in_nodata = nds
		else:
			# If the source dataset has NODATA, use it.
			self.in_nodata = []
			for i in range(1, self.in_ds.RasterCount+1):
				if self.in_ds.GetRasterBand(i).GetNoDataValue() != None:
					self.in_nodata.append( self.in_ds.GetRasterBand(i).GetNoDataValue() )

		if self.options.verbose:
			print "NODATA: %s" % self.in_nodata

		# INIT DEST
		if self.options.init_dest is not None:
			if self.options.tile_format == "jpeg":
				if self.in_ds.RasterCount == 4:
					nbands = 3
				else:
					nbands = self.in_ds.RasterCount

				nds = map(float, self.options.init_dest.split(','))

				if len(nds) == 1:
					init_dest = nds * nbands
				elif len(nds) == nbands:
					init_dest = nds
				else:
					print "WARNING: you suplied %d '--init-dest' values but the dataset has %d data bands" % (len(nds), nbands)
					init_dest = None
			else:
				init_dest = None
				print "WARNING: --init-dest can be used only with 'jpeg' tile format"
		else:
			if self.options.tile_format == "jpeg":
				init_dest = [255,255,255]
			else:
				init_dest = None

		#
		# Here we should have RGBA input dataset opened in self.in_ds
		#

		if self.options.verbose:
			print "Preprocessed file:", "( %sP x %sL - %s bands)" % (self.in_ds.RasterXSize, self.in_ds.RasterYSize, self.in_ds.RasterCount)

		# Spatial Reference System of the input raster


		self.in_srs = None
		
		if self.options.s_srs:
			self.in_srs = osr.SpatialReference()
			self.in_srs.SetFromUserInput(self.options.s_srs)
			self.in_srs_wkt = self.in_srs.ExportToWkt()
		else:
			self.in_srs_wkt = self.in_ds.GetProjection()
			if not self.in_srs_wkt and self.in_ds.GetGCPCount() != 0:
				self.in_srs_wkt = self.in_ds.GetGCPProjection()
			if self.in_srs_wkt:
				self.in_srs = osr.SpatialReference()
				self.in_srs.ImportFromWkt(self.in_srs_wkt)
			#elif self.options.profile != 'raster':
			#	self.error("There is no spatial reference system info included in the input file.","You should run gdal2tiles with --s_srs EPSG:XXXX or similar.")

		# Spatial Reference System of tiles
		
		self.out_srs = osr.SpatialReference()

		if self.options.profile == 'mercator':
			self.out_srs.ImportFromEPSG(3857)
		elif self.options.profile in ('geodetic', 'gearth', 'garmin'):
			self.out_srs.ImportFromEPSG(4326)
		else:
			self.out_srs = self.in_srs
		
		# Are the reference systems the same? Reproject if necessary.

		self.out_ds = None

		if self.options.profile in ('mercator', 'geodetic', 'gearth', 'garmin'):

			if (self.in_ds.GetGeoTransform() == (0.0, 1.0, 0.0, 0.0, 0.0, 1.0)) and (self.in_ds.GetGCPCount() == 0):
				self.error("There is no georeference - neither affine transformation (worldfile) nor GCPs. You can generate only 'raster' profile tiles.",
				"Either gdal2tiles with parameter -p 'raster' or use another GIS software for georeference e.g. gdal_transform -gcp / -a_ullr / -a_srs")
				
			if self.in_srs:
				
				if (self.in_srs.ExportToProj4() != self.out_srs.ExportToProj4()) or (self.in_ds.GetGCPCount() != 0):
					
					# Generation of VRT dataset in tile projection, default 'nearest neighbour' warping
					self.out_ds = gdal.AutoCreateWarpedVRT( self.in_ds, self.in_srs_wkt, self.out_srs.ExportToWkt() )
					
					# TODO: HIGH PRIORITY: Correction of AutoCreateWarpedVRT according the max zoomlevel for correct direct warping!!!
					
					if self.options.verbose:
						print "Warping of the raster by AutoCreateWarpedVRT (result saved into 'tiles.vrt')"
						self.out_ds.GetDriver().CreateCopy("tiles.vrt", self.out_ds)
						
					# Note: self.in_srs and self.in_srs_wkt contain still the non-warped reference system!!!
						
					# Correction of AutoCreateWarpedVRT for NODATA values
					if self.in_nodata != []:
						import tempfile
						tempfilename = tempfile.mktemp('-gdal2tiles.vrt')
						self.out_ds.GetDriver().CreateCopy(tempfilename, self.out_ds)
						# open as a text file
						s = open(tempfilename).read()
						# Add the warping options
						s = s.replace("""<GDALWarpOptions>""","""<GDALWarpOptions>
	  <Option name="UNIFIED_SRC_NODATA">YES</Option>
	  <Option name="INIT_DEST">NO_DATA</Option>""")
						# replace BandMapping tag for NODATA bands....
						if init_dest is None:
							dstnodata = self.in_nodata
						else:
							dstnodata = init_dest
						for i in range(len(self.in_nodata)):
							s = s.replace("""<BandMapping src="%i" dst="%i"/>""" % ((i+1),(i+1)),"""<BandMapping src="%i" dst="%i">
	      <SrcNoDataReal>%i</SrcNoDataReal>
	      <SrcNoDataImag>0</SrcNoDataImag>
	      <DstNoDataReal>%i</DstNoDataReal>
	      <DstNoDataImag>0</DstNoDataImag>
	    </BandMapping>""" % ((i+1), (i+1), self.in_nodata[i], dstnodata[i]))
						# save the corrected VRT
						open(tempfilename,"w").write(s)
						# open by GDAL as self.out_ds
						self.out_ds = gdal.Open(tempfilename) #, gdal.GA_ReadOnly)
						# delete the temporary file
						os.unlink(tempfilename)

						# set NODATA_VALUE metadata
						self.out_ds.SetMetadataItem('NODATA_VALUES','%s' % " ".join(str(int(f)) for f in self.in_nodata))

						if self.options.verbose:
							print "Modified warping result saved into 'tiles1.vrt'"
							open("tiles1.vrt","w").write(s)

					# -----------------------------------
					# Correction of AutoCreateWarpedVRT for Mono (1 band) and RGB (3 bands) files without NODATA:
					# equivalent of gdalwarp -dstalpha
					elif self.in_nodata == [] and self.out_ds.RasterCount in (1,3):
						import tempfile
						tempfilename = tempfile.mktemp('-gdal2tiles.vrt')
						self.out_ds.GetDriver().CreateCopy(tempfilename, self.out_ds)
						# open as a text file
						s = open(tempfilename).read()
						# Add the warping options
						s = s.replace("""<BlockXSize>""","""<VRTRasterBand dataType="Byte" band="%i" subClass="VRTWarpedRasterBand">
    <ColorInterp>Alpha</ColorInterp>
  </VRTRasterBand>
  <BlockXSize>""" % (self.out_ds.RasterCount + 1))
						s = s.replace("""</GDALWarpOptions>""", """<DstAlphaBand>%i</DstAlphaBand>
  </GDALWarpOptions>""" % (self.out_ds.RasterCount + 1))
						if init_dest is None:
							init_dest_str = "0"
						else:
							init_dest_str = ",".join(str(f) for f in init_dest)
						s = s.replace("""</WorkingDataType>""", """</WorkingDataType>
    <Option name="INIT_DEST">%s</Option>""" % init_dest_str)
						# save the corrected VRT
						open(tempfilename,"w").write(s)
						# open by GDAL as self.out_ds
						self.out_ds = gdal.Open(tempfilename) #, gdal.GA_ReadOnly)
						# delete the temporary file
						os.unlink(tempfilename)

						if self.options.verbose:
							print "Modified -dstalpha warping result saved into 'tiles1.vrt'"
							open("tiles1.vrt","w").write(s)

					elif init_dest is not None:
						import tempfile
						tempfilename = tempfile.mktemp('-gdal2tiles.vrt')
						self.out_ds.GetDriver().CreateCopy(tempfilename, self.out_ds)
						# open as a text file
						s = open(tempfilename).read()
						# Add the warping options
						s = s.replace("""</WorkingDataType>""", """</WorkingDataType>
    <Option name="INIT_DEST">%s</Option>""" % ",".join(str(f) for f in init_dest))
						# save the corrected VRT
						open(tempfilename,"w").write(s)
						# open by GDAL as self.out_ds
						self.out_ds = gdal.Open(tempfilename) #, gdal.GA_ReadOnly)
						# delete the temporary file
						os.unlink(tempfilename)

						if self.options.verbose:
							print "Modified warping result saved into 'tiles1.vrt'"
							open("tiles1.vrt","w").write(s)

					# For raster with 4-bands: 4th unknown band set to alpha
					if (self.out_ds.RasterCount == 4
						and self.out_ds.GetRasterBand(4).GetRasterColorInterpretation() == gdal.GCI_Undefined):
						self.out_ds.GetRasterBand(4).SetRasterColorInterpretation(gdal.GCI_AlphaBand)

					s = '''
					'''
						
			else:
				self.error("Input file has unknown SRS.", "Use --s_srs ESPG:xyz (or similar) to provide source reference system." )

			if self.out_ds and self.options.verbose:
				print "Projected file:", "tiles.vrt", "( %sP x %sL - %s bands)" % (self.out_ds.RasterXSize, self.out_ds.RasterYSize, self.out_ds.RasterCount)
		
		if not self.out_ds:
			self.out_ds = self.in_ds

		#
		# Here we should have a raster (out_ds) in the correct Spatial Reference system
		#

		# KML test
		self.isepsg4326 = False
		srs4326 = osr.SpatialReference()
		srs4326.ImportFromEPSG(4326)
		if self.out_srs and srs4326.ExportToProj4() == self.out_srs.ExportToProj4():
			self.kml = True
			self.isepsg4326 = True
			if self.options.verbose:
				print "KML autotest OK!"

		# Instantiate image output.
		self.image_output = ImageOutput(self.options.tile_format, self.out_ds, self.tilesize,
										self.options.resampling, init_dest, self.output,
										self.options.verbose)

		# Read the georeference 

		self.out_gt = self.out_ds.GetGeoTransform()
			
		#originX, originY = self.out_gt[0], self.out_gt[3]
		#pixelSize = self.out_gt[1] # = self.out_gt[5]
		
		# Test the size of the pixel
		
		# MAPTILER - COMMENTED
		#if self.out_gt[1] != (-1 * self.out_gt[5]) and self.options.profile != 'raster':
			# TODO: Process corectly coordinates with are have swichted Y axis (display in OpenLayers too)
			#self.error("Size of the pixel in the output differ for X and Y axes.")
			
		# Report error in case rotation/skew is in geotransform (possible only in 'raster' profile)
		if (self.out_gt[2], self.out_gt[4]) != (0,0):
			self.error("Georeference of the raster contains rotation or skew. Such raster is not supported. Please use gdalwarp first.")
			# TODO: Do the warping in this case automaticaly

		#
		# Here we expect: pixel is square, no rotation on the raster
		#

		# Output Bounds - coordinates in the output SRS
		self.ominx = self.out_gt[0]
		self.omaxx = self.out_gt[0]+self.out_ds.RasterXSize*self.out_gt[1]
		self.omaxy = self.out_gt[3]
		self.ominy = self.out_gt[3]-self.out_ds.RasterYSize*self.out_gt[1]
		# Note: maybe round(x, 14) to avoid the gdal_translate behaviour, when 0 becomes -1e-15

		if self.options.verbose:
			print "Bounds (output srs):", round(self.ominx, 13), self.ominy, self.omaxx, self.omaxy

		#
		# Calculating ranges for tiles in different zoom levels
		#

		if self.options.profile == 'mercator':

			self.mercator = GlobalMercator() # from globalmaptiles.py
			
			# Function which generates SWNE in LatLong for given tile
			self.tileswne = self.mercator.TileLatLonBounds

			# Generate table with min max tile coordinates for all zoomlevels
			self.tminmax = range(0,32)
			for tz in range(0, 32):
				tminx, tminy = self.mercator.MetersToTile( self.ominx, self.ominy, tz )
				tmaxx, tmaxy = self.mercator.MetersToTile( self.omaxx, self.omaxy, tz )
				# crop tiles extending world limits (+-180,+-90)
				tminx, tminy = max(0, tminx), max(0, tminy)
				tmaxx, tmaxy = min(2**tz-1, tmaxx), min(2**tz-1, tmaxy)
				self.tminmax[tz] = (tminx, tminy, tmaxx, tmaxy)

			# TODO: Maps crossing 180E (Alaska?)

			# Get the minimal zoom level (map covers area equivalent to one tile) 
			if self.tminz == None:
				self.tminz = self.mercator.ZoomForPixelSize( self.out_gt[1] * max( self.out_ds.RasterXSize, self.out_ds.RasterYSize) / float(self.tilesize) )

			# Get the maximal zoom level (closest possible zoom level up on the resolution of raster)
			if self.tmaxz == None:
				self.tmaxz = self.mercator.ZoomForPixelSize( self.out_gt[1] )
			
			if self.options.verbose:
				print "Bounds (latlong):", self.mercator.MetersToLatLon( self.ominx, self.ominy), self.mercator.MetersToLatLon( self.omaxx, self.omaxy)
				print 'MinZoomLevel:', self.tminz
				print "MaxZoomLevel:", self.tmaxz, "(", self.mercator.Resolution( self.tmaxz ),")"

		if self.options.profile == 'geodetic':

			self.geodetic = GlobalGeodetic() # from globalmaptiles.py

			# Function which generates SWNE in LatLong for given tile
			self.tileswne = self.geodetic.TileLatLonBounds
			
			# Generate table with min max tile coordinates for all zoomlevels
			self.tminmax = range(0,32)
			for tz in range(0, 32):
				tminx, tminy = self.geodetic.LatLonToTile( self.ominx, self.ominy, tz )
				tmaxx, tmaxy = self.geodetic.LatLonToTile( self.omaxx, self.omaxy, tz )
				# crop tiles extending world limits (+-180,+-90)
				tminx, tminy = max(0, tminx), max(0, tminy)
				tmaxx, tmaxy = min(2**(tz+1)-1, tmaxx), min(2**tz-1, tmaxy)
				self.tminmax[tz] = (tminx, tminy, tmaxx, tmaxy)
				
			# TODO: Maps crossing 180E (Alaska?)

			# Get the maximal zoom level (closest possible zoom level up on the resolution of raster)
			if self.tminz == None:
				self.tminz = self.geodetic.ZoomForPixelSize( self.out_gt[1] * max( self.out_ds.RasterXSize, self.out_ds.RasterYSize) / float(self.tilesize) )

			# Get the maximal zoom level (closest possible zoom level up on the resolution of raster)
			if self.tmaxz == None:
				self.tmaxz = self.geodetic.ZoomForPixelSize( self.out_gt[1] )
			
			if self.options.verbose:
				print "Bounds (latlong):", self.ominx, self.ominy, self.omaxx, self.omaxy
					
		if self.options.profile in ('raster', 'gearth', 'garmin'):
			
			log2 = lambda x: math.log10(x) / math.log10(2) # log2 (base 2 logarithm)
			
			self.nativezoom = int(max( math.ceil(log2(self.out_ds.RasterXSize/float(self.tilesize))),
			                           math.ceil(log2(self.out_ds.RasterYSize/float(self.tilesize)))))
			
			if self.options.verbose:
				print "Native zoom of the raster:", self.nativezoom

			# Get the minimal zoom level (whole raster in one tile)
			if self.tminz == None:
				self.tminz = 0

			# Get the maximal zoom level (native resolution of the raster)
			if self.tmaxz == None:
				self.tmaxz = self.nativezoom

			# Garmin has maximally 100 tiles - lower the tmaxz if necessary
			if self.options.profile == 'garmin':
				tno = math.ceil(self.out_ds.RasterXSize / self.tilesize) * math.ceil(self.out_ds.RasterYSize / self.tilesize)
				for tz in range(self.tmaxz, 1, -1):
					if tno > 100:
						tno /= 4
						self.tmaxz -= 1 
						print "Warning: GARMIN has a limit 100 tiles per device: lowering the max zoom level to:", self.tmaxz
					else:
						continue

			# Force only one zoom level for the 'garmin' tile profile
			if self.options.profile == 'garmin':
				self.tminz = self.tmaxz

			# Generate table with min max tile coordinates for all zoomlevels
			self.tminmax = range(0, self.tmaxz+1)
			self.tsize = range(0, self.tmaxz+1)
			for tz in range(0, self.tmaxz+1):
				tsize = 2.0**(self.nativezoom-tz)*self.tilesize
				tminx, tminy = 0, 0
				tmaxx = int(math.ceil( self.out_ds.RasterXSize / tsize )) - 1
				tmaxy = int(math.ceil( self.out_ds.RasterYSize / tsize )) - 1
				self.tsize[tz] = math.ceil(tsize)
				self.tminmax[tz] = (tminx, tminy, tmaxx, tmaxy)

			# Function which generates SWNE in LatLong for given tile
			if self.kml and self.in_srs_wkt:
				self.ct = osr.CoordinateTransformation(self.in_srs, srs4326)

				def rastertileswne(x,y,z):
					pixelsizex = (2**(self.nativezoom-z) * self.out_gt[1]) # X-pixel size in level
					pixelsizey = (2**(self.nativezoom-z) * self.out_gt[5]) # Y-pixel size in level (usually -1*pixelsizex)
					west = self.out_gt[0] + x*self.tilesize*pixelsizex
					east = west + self.tilesize*pixelsizex
					south = self.ominy + y*self.tilesize*pixelsizex
					north = south + self.tilesize*pixelsizex
					if not self.isepsg4326:
						# Transformation to EPSG:4326 (WGS84 datum)
						west, south = self.ct.TransformPoint(west, south)[:2]
						east, north = self.ct.TransformPoint(east, north)[:2]
					return south, west, north, east

				self.tileswne = rastertileswne
			else:
				self.tileswne = lambda x, y, z: (0,0,0,0)

	# -------------------------------------------------------------------------
	def generate_metadata(self):
		"""Generation of main metadata files and HTML viewers (metadata related to particular tiles are generated during the tile processing)."""
		
		if not os.path.exists(self.output):
			os.makedirs(self.output)

		if self.options.profile == 'mercator':
			
			south, west = self.mercator.MetersToLatLon( self.ominx, self.ominy)
			north, east = self.mercator.MetersToLatLon( self.omaxx, self.omaxy)
			south, west = max(-85.05112878, south), max(-180.0, west)
			north, east = min(85.05112878, north), min(180.0, east)
			self.swne = (south, west, north, east)

			# Generate googlemaps.html
			if self.options.webviewer in ('all','google') and self.options.profile == 'mercator':
				if not self.options.resume or not os.path.exists(os.path.join(self.output, 'googlemaps.html')):
					f = open(os.path.join(self.output, 'googlemaps.html'), 'w')
					f.write( self.generate_googlemaps() )
					f.close()

			# Generate openlayers.html
			if self.options.webviewer in ('all','openlayers'):
				if not self.options.resume or not os.path.exists(os.path.join(self.output, 'openlayers.html')):
					f = open(os.path.join(self.output, 'openlayers.html'), 'w')
					f.write( self.generate_openlayers() )
					f.close()

		elif self.options.profile == 'geodetic':
			
			west, south = self.ominx, self.ominy
			east, north = self.omaxx, self.omaxy
			south, west = max(-90.0, south), max(-180.0, west)
			north, east = min(90.0, north), min(180.0, east)
			self.swne = (south, west, north, east)
			
			# Generate openlayers.html
			if self.options.webviewer in ('all','openlayers'):
				if not self.options.resume or not os.path.exists(os.path.join(self.output, 'openlayers.html')):
					f = open(os.path.join(self.output, 'openlayers.html'), 'w')
					f.write( self.generate_openlayers() )
					f.close()			

		elif self.options.profile in ['raster','gearth','garmin']:
			
			west, south = self.ominx, self.ominy
			east, north = self.omaxx, self.omaxy

			self.swne = (south, west, north, east)
			
			# Generate openlayers.html
			if self.options.webviewer in ('all','openlayers'):
				if not self.options.resume or not os.path.exists(os.path.join(self.output, 'openlayers.html')):
					f = open(os.path.join(self.output, 'openlayers.html'), 'w')
					f.write( self.generate_openlayers() )
					f.close()			


		# Generate tilemapresource.xml.
		if (self.options.tile_format != 'hybrid' and self.options.profile != 'garmin'
			and (not self.options.resume or not os.path.exists(os.path.join(self.output, 'tilemapresource.xml')))):
			f = open(os.path.join(self.output, 'tilemapresource.xml'), 'w')
			f.write( self.generate_tilemapresource())
			f.close()

	# -------------------------------------------------------------------------
	def generate_base_tiles(self):
		"""Generation of the base tiles (the lowest in the pyramid) directly from the input raster"""

		gdal.SetConfigOption("GDAL_PAM_ENABLED", "NO")

		print "Generating Base Tiles:"
		
		if self.options.verbose:
			#mx, my = self.out_gt[0], self.out_gt[3] # OriginX, OriginY
			#px, py = self.mercator.MetersToPixels( mx, my, self.tmaxz)
			#print "Pixel coordinates:", px, py, (mx, my)
			print
			print "Tiles generated from the max zoom level:"
			print "----------------------------------------"
			print


		# Set the bounds
		tminx, tminy, tmaxx, tmaxy = self.tminmax[self.tmaxz]
		querysize = self.querysize

		# Just the center tile
		#tminx = tminx+ (tmaxx - tminx)/2
		#tminy = tminy+ (tmaxy - tminy)/2
		#tmaxx = tminx
		#tmaxy = tminy

		#print tminx, tminy, tmaxx, tmaxy
		tcount = (1+abs(tmaxx-tminx)) * (1+abs(tmaxy-tminy))
		#print tcount
		ti = 0
		
		ds = self.out_ds
		tz = self.tmaxz
		for ty in range(tmaxy, tminy-1, -1): #range(tminy, tmaxy+1):
			for tx in range(tminx, tmaxx+1):

				if self.stopped:
					break
				ti += 1

				if self.options.verbose:
					print ti, '/', tcount, self.get_verbose_tile_name(tx, ty, tz)

				if self.options.resume:
					exists = self.image_output.tile_exists(tx, ty, tz)
					if exists and self.options.verbose:
						print "\tTile generation skipped because of --resume"
				else:
					exists = False

				if not exists:
					# Don't scale up by nearest neighbour, better change the querysize
					# to the native resolution (and return smaller query tile) for scaling
					if self.options.profile in ('mercator','geodetic'):
						if self.options.profile == 'mercator':
							# Tile bounds in EPSG:900913
							b = self.mercator.TileBounds(tx, ty, tz)
						elif self.options.profile == 'geodetic':
							b = self.geodetic.TileBounds(tx, ty, tz)

						rb, wb = self.geo_query( ds, b[0], b[3], b[2], b[1])
						nativesize = wb[0]+wb[2] # Pixel size in the raster covering query geo extent
						if self.options.verbose:
							print "\tNative Extent (querysize",nativesize,"): ", rb, wb

						querysize = self.querysize
						# Tile bounds in raster coordinates for ReadRaster query
						rb, wb = self.geo_query( ds, b[0], b[3], b[2], b[1], querysize=querysize)

						rx, ry, rxsize, rysize = rb
						wx, wy, wxsize, wysize = wb
					else: # 'raster' or 'gearth' or 'garmin' profile:
						tsize = int(self.tsize[tz]) # tilesize in raster coordinates for actual zoom
						xsize = self.out_ds.RasterXSize # size of the raster in pixels
						ysize = self.out_ds.RasterYSize
						if tz >= self.nativezoom:
							querysize = self.tilesize # int(2**(self.nativezoom-tz) * self.tilesize)

						rx = (tx) * tsize
						rxsize = 0
						if tx == tmaxx:
							rxsize = xsize % tsize
						if rxsize == 0:
							rxsize = tsize

						rysize = 0
						if ty == tmaxy:
							rysize = ysize % tsize
						if rysize == 0:
							rysize = tsize
						ry = ysize - (ty * tsize) - rysize

						wx, wy = 0, 0
						
						wxsize, wysize = int(rxsize/float(tsize) * querysize), int(rysize/float(tsize) * querysize)
						if wysize != querysize:
							wy = querysize - wysize

					xyzzy = Xyzzy(querysize, rx, ry, rxsize, rysize, wx, wy, wxsize, wysize)

					try:
						self.image_output.write_base_tile(tx, ty, tz, xyzzy)
					except ImageOutputException, e:
						self.error("'%d/%d/%d': %s" % (tz, tx, ty, e.message))

				if not self.options.verbose or self.is_subprocess:
					self.progressbar( ti / float(tcount) )

	# -------------------------------------------------------------------------
	def generate_overview_tiles(self):
		"""Generation of the overview tiles (higher in the pyramid) based on existing tiles"""

		gdal.SetConfigOption("GDAL_PAM_ENABLED", "NO")

		print "Generating Overview Tiles:"
		
		if self.options.profile == 'garmin': # no overview tiles for 'garmin'
			return

		# Usage of existing tiles: from 4 underlying tiles generate one as overview.
		
		tcount = 0
		for tz in range(self.tmaxz-1, self.tminz-1, -1):
			tminx, tminy, tmaxx, tmaxy = self.tminmax[tz]
			tcount += (1+abs(tmaxx-tminx)) * (1+abs(tmaxy-tminy))

		ti = 0
		
		# querysize = tilesize * 2

		for tz in range(self.tmaxz-1, self.tminz-1, -1):

			tminx, tminy, tmaxx, tmaxy = self.tminmax[tz]
			for ty in range(tmaxy, tminy-1, -1): #range(tminy, tmaxy+1):
				for tx in range(tminx, tmaxx+1):
					
					if self.stopped:
						break
						
					ti += 1

					if self.options.verbose:
						print ti, '/', tcount, self.get_verbose_tile_name(tx, ty, tz)

					if self.options.resume:
						exists = self.image_output.tile_exists(tx, ty, tz)
						if exists and self.options.verbose:
							print "\tTile generation skipped because of --resume"
					else:
						exists = False

					if not exists:
						try:
							self.image_output.write_overview_tile(tx, ty, tz)
						except ImageOutputException, e:
							self.error("'%d/%d/%d': %s" % (tz, tx, ty, e.message))

					if not self.options.verbose or self.is_subprocess:
						self.progressbar( ti / float(tcount) )

	# -------------------------------------------------------------------------
	def generate_kml(self):
		if not self.kml:
			return

		# The KMZ specific to 'garmin' profile
		if self.options.profile == 'garmin':
			if os.path.basename( self.output ):
				zipname = os.path.basename( self.output ) + '.kmz'
			else:
				zipname = os.path.basename( self.output[:-1] + '.kmz' )
			f = ZipFile(os.path.join( self.output, zipname), "w", ZIP_DEFLATED)
			kml_tiles = {}
			children_kml = []
			tz = self.tmaxz
			tminx, tminy, tmaxx, tmaxy = self.tminmax[tz]
			for ty in range(tminy, tmaxy+1):
				for tx in range(tminx, tmaxx+1):
					image_format = self.image_output.try_to_use_existing_tile(tx, ty, tz)
					if image_format is None:
						continue
					filename = self.image_output.get_full_path(tx, ty, tz, format_extension[image_format])
					f.write(filename, get_tile_filename(tx, ty, tz, format_extension[image_format]), ZIP_STORED)
					os.unlink(filename)

					d = self.get_kml_dict(tx, ty, tz, image_format, draworder = 50)
					children_kml.append( self.generate_garmin_kml(d) )
			
			f.writestr("doc.kml", self.generate_document_kml(self.options.title, "".join(children_kml)))
			f.close()
			import shutil
			shutil.rmtree( os.path.join(self.output, str(tz)) )
			return

		# Base level KML.
		kml_tiles = {}
		tz = self.tmaxz
		tminx, tminy, tmaxx, tmaxy = self.tminmax[tz]
		for ty in range(tminy, tmaxy+1):
			for tx in range(tminx, tmaxx+1):
				image_format = self.image_output.try_to_use_existing_tile(tx, ty, tz)
				if image_format is None:
					continue

				d = self.get_kml_dict(tx, ty, tz, image_format)

				if self.kml_depth == 1 or self.tmaxz == self.tminz:
					self.write_kml_tile(tx, ty, tz, self.generate_node_kml(d, []))
					kml_tiles[tx,ty,tz] = self.generate_link_kml(d)
				else:
					kml_tiles[tx,ty,tz] = self.generate_leaf_kml(d)

		# Overviews KML.
		for tz in range(self.tmaxz-1, self.tminz-1, -1):
			tminx, tminy, tmaxx, tmaxy = self.tminmax[tz]
			for ty in range(tminy, tmaxy+1):
				for tx in range(tminx, tmaxx+1):
					image_format = self.image_output.try_to_use_existing_tile(tx, ty, tz)
					if image_format is None:
						continue

					d = self.get_kml_dict(tx, ty, tz, image_format)

					children = [kml_tiles[x,y,tz+1]
								for y in range(2*ty, 2*ty + 2)
								for x in range(2*tx, 2*tx + 2)
								if (x,y,tz+1) in kml_tiles]

					node_kml = self.generate_node_kml(d, children)
					if (self.tmaxz-tz + 1) % self.kml_depth == 0 or tz == self.tminz:
						self.write_kml_tile(tx, ty, tz, node_kml)
						kml_tiles[tx,ty,tz] = self.generate_link_kml(d)
					else:
						kml_tiles[tx,ty,tz] = node_kml

		# Root KML.
		tminx, tminy, tmaxx, tmaxy = self.tminmax[self.tminz]
		children_kml = [kml_tiles[x,y,self.tminz]
						for y in range(tminy, tmaxy+1)
						for x in range(tminx, tmaxx+1)
						if (x,y,self.tminz) in kml_tiles]
		
		lookat = computeFitLookAt(self.swne[1], self.swne[0], self.swne[3], self.swne[2])
		lookat_kml = self.generate_lookat_kml_block(lookat[0], lookat[1], lookat[2])
		self.write_kml_file("doc.kml", self.options.title, lookat_kml+"\n".join(children_kml))

	# -------------------------------------------------------------------------
	def geo_query(self, ds, ulx, uly, lrx, lry, querysize = 0):
		"""For given dataset and query in cartographic coordinates
		returns parameters for ReadRaster() in raster coordinates and
		x/y shifts (for border tiles). If the querysize is not given, the
		extent is returned in the native resolution of dataset ds."""

		geotran = ds.GetGeoTransform()
		rx= int((ulx - geotran[0]) / geotran[1] + 0.001)
		ry= int((uly - geotran[3]) / geotran[5] + 0.001)
		rxsize= int((lrx - ulx) / geotran[1] + 0.5)
		rysize= int((lry - uly) / geotran[5] + 0.5)

		if not querysize:
			wxsize, wysize = rxsize, rysize
		else:
			wxsize, wysize = querysize, querysize

		# Coordinates should not go out of the bounds of the raster
		wx = 0
		if rx < 0:
			rxshift = abs(rx)
			wx = int( wxsize * (float(rxshift) / rxsize) )
			wxsize = wxsize - wx
			rxsize = rxsize - int( rxsize * (float(rxshift) / rxsize) )
			rx = 0
		if rx+rxsize > ds.RasterXSize:
			wxsize = int( wxsize * (float(ds.RasterXSize - rx) / rxsize) )
			rxsize = ds.RasterXSize - rx

		wy = 0
		if ry < 0:
			ryshift = abs(ry)
			wy = int( wysize * (float(ryshift) / rysize) )
			wysize = wysize - wy
			rysize = rysize - int( rysize * (float(ryshift) / rysize) )
			ry = 0
		if ry+rysize > ds.RasterYSize:
			wysize = int( wysize * (float(ds.RasterYSize - ry) / rysize) )
			rysize = ds.RasterYSize - ry

		return (rx, ry, rxsize, rysize), (wx, wy, wxsize, wysize)

	# -------------------------------------------------------------------------
	def write_kml_tile(self, tx, ty, tz, kml):
		if self.options.kmz:
			filename = get_tile_filename(tx, ty, tz, "kmz")
			self.write_kmz_file(filename, filename, kml)
		else:
			filename = get_tile_filename(tx, ty, tz, "kml")
			self.write_kml_file(filename, filename, kml)

	def write_kml_file(self, filename, title, content):
		f = open(os.path.join(self.output, filename), 'w')
		f.write(self.generate_document_kml(title, content))
		f.close()

	def write_kmz_file(self, filename, title, content):
		f = ZipFile(os.path.join(self.output, filename), "w", ZIP_DEFLATED)
		f.writestr("doc.kml", self.generate_document_kml(title, content))
		f.close()

	def generate_node_kml(self, d, children):
		"""Return KML describing tile image and its children."""
		return self.generate_leaf_kml(d, "\n".join(children))

	def generate_garmin_kml(self, d ):
		"""Return Garmin KML block describing an tile image."""
		return ("""
      <GroundOverlay>
        <Icon>
          <href>%(image_url)s</href>
          <DrawOrder>%(draw_order)d</DrawOrder>
        </Icon>
        <LatLonBox>
          <north>%(north).14f</north>
          <south>%(south).14f</south>
          <east>%(east).14f</east>
          <west>%(west).14f</west>
        </LatLonBox>
      </GroundOverlay>""" % d )

	def generate_leaf_kml(self, d, content=""):
		"""Return KML describing tile image and insert content."""
		return ("""\
    <Folder>
      <Region>
        <Lod>
          <minLodPixels>%(minlodpixels)d</minLodPixels>
          <maxLodPixels>%(maxlodpixels)d</maxLodPixels>
        </Lod>
        <LatLonAltBox>
          <north>%(north).14f</north>
          <south>%(south).14f</south>
          <east>%(east).14f</east>
          <west>%(west).14f</west>
        </LatLonAltBox>
      </Region>
      <GroundOverlay>
        <drawOrder>%(draw_order)d</drawOrder>
        <Icon>
          <href>%(image_url)s</href>
        </Icon>
        <LatLonBox>
          <north>%(north).14f</north>
          <south>%(south).14f</south>
          <east>%(east).14f</east>
          <west>%(west).14f</west>
        </LatLonBox>
      </GroundOverlay>""" % d
	  + """\
%s
    </Folder>""" % content)

	def generate_link_kml(self, d):
		"""Return KML linking to the tile."""
		return """\
    <NetworkLink>
      <name>%(image_filename)s</name>
      <Region>
        <Lod>
          <minLodPixels>%(minlodpixels)d</minLodPixels>
          <maxLodPixels>-1</maxLodPixels>
        </Lod>
        <LatLonAltBox>
          <north>%(north).14f</north>
          <south>%(south).14f</south>
          <east>%(east).14f</east>
          <west>%(west).14f</west>
        </LatLonAltBox>
      </Region>
      <Link>
        <href>%(link_url)s</href>
        <viewRefreshMode>onRegion</viewRefreshMode>
      </Link>
    </NetworkLink>""" % d

	def generate_document_kml(self, title, content):
		"""Return full KML document with given title and content."""
		return """\
<?xml version="1.0" encoding="utf-8"?>
<kml xmlns="http://earth.google.com/kml/2.1">
  <Document>
    <name>%s</name>
    <description></description>
    <Style>
      <ListStyle id="hideChildren">
        <listItemType>checkHideChildren</listItemType>
      </ListStyle>
    </Style>
%s
  </Document>
</kml>""" % (title.replace('\\','/'), content)

	def generate_lookat_kml_block(self, lng, lat, viewrange):
		"""Return the KML string containing correct <LookAt> block"""
		return """
    <LookAt>
      <longitude>%.14f</longitude>
      <latitude>%.14f</latitude>
      <altitude>0</altitude>
      <range>%.f</range>
      <tilt>0</tilt>
      <heading>0</heading>
    </LookAt>
""" % (lng, lat, viewrange)

	def get_kml_dict(self, tx, ty, tz, image_format, draworder = 0):
		"""Return dictionary describing KML info about tile to be used in templates."""
		d = {}

		d["south"], d["west"], d["north"], d["east"] = self.tileswne(tx, ty, tz)

		image_filename = get_tile_filename(tx, ty, tz, format_extension[image_format])
		d["image_filename"] = image_filename
		d["image_filename"] = d["image_filename"].replace("\\","/")

		if self.options.url is None:
			d["image_url"] = "../../%s" % image_filename
		else:
			d["image_url"] = "%s%s" % (self.options.url, image_filename)
		d["image_url"] = d["image_url"].replace("\\","/")

		url = self.options.url
		if url is None:
			# Top level KML is linked from `doc.kml' and it needs different path.
			if tz == self.tminz:
				url = ""
			else:
				url = "../../"

		if self.options.kmz:
			extension = "kmz"
		else:
			extension = "kml"

		d["link_url"] = "%s%s" % (url, get_tile_filename(tx, ty, tz, extension))
		d["link_url"] = d["link_url"].replace("\\","/")

		d["minlodpixels"] = int(self.tilesize / 2)
		d["maxlodpixels"] = -1 # int(self.tilesize * 8)

		if tx == 0:
			d["draw_order"] = draworder + 2 * tz + 1
		else:
			d["draw_order"] = draworder + 2 * tz

		return d

	def get_verbose_tile_name(self, tx, ty, tz):
		if self.options.tile_format == "hybrid":
			extension = "?"
		else:
			extension = format_extension[self.image_output.format]

		return self.image_output.get_full_path(tx, ty, tz, extension)

	# -------------------------------------------------------------------------
	def generate_tilemapresource(self):
		"""
	    Template for tilemapresource.xml. Returns filled string. Expected variables:
	      title, north, south, east, west, isepsg4326, projection, publishurl,
	      zoompixels, tilesize, tileformat, profile
		"""

		args = {}
		args['title'] = self.options.title
		args['south'], args['west'], args['north'], args['east'] = self.swne
		args['tilesize'] = self.tilesize
		args['tileformat'] = format_extension[self.image_output.format]
		args['mime'] = format_mime[self.image_output.format]
		args['publishurl'] = "" if self.options.url is None else self.options.url
		args['profile'] = self.options.profile
		
		if self.options.profile == 'mercator':
			args['srs'] = "EPSG:3857"
		elif self.options.profile in ('geodetic', 'gearth'):
			args['srs'] = "EPSG:4326"
		elif self.options.s_srs:
			args['srs'] = self.options.s_srs
		elif self.out_srs:
			args['srs'] = self.out_srs.ExportToWkt()
		else:
			args['srs'] = ""

		s = """<?xml version="1.0" encoding="utf-8"?>
	<TileMap version="1.0.0" tilemapservice="http://tms.osgeo.org/1.0.0">
	  <Title>%(title)s</Title>
	  <Abstract></Abstract>
	  <SRS>%(srs)s</SRS>
	  <BoundingBox minx="%(south).14f" miny="%(west).14f" maxx="%(north).14f" maxy="%(east).14f"/>
	  <Origin x="%(south).14f" y="%(west).14f"/>
	  <TileFormat width="%(tilesize)d" height="%(tilesize)d" mime-type="%(mime)s" extension="%(tileformat)s"/>
	  <TileSets profile="%(profile)s">
""" % args
		for z in range(self.tminz, self.tmaxz+1):
			if self.options.profile == 'raster':
				s += """	    <TileSet href="%s%d" units-per-pixel="%.14f" order="%d"/>\n""" % (args['publishurl'], z, (2**(self.nativezoom-z) * self.out_gt[1]), z)
			elif self.options.profile == 'mercator':
				s += """	    <TileSet href="%s%d" units-per-pixel="%.14f" order="%d"/>\n""" % (args['publishurl'], z, 156543.0339/2**z, z)
			elif self.options.profile == 'geodetic':
				s += """	    <TileSet href="%s%d" units-per-pixel="%.14f" order="%d"/>\n""" % (args['publishurl'], z, 0.703125/2**z, z)
		s += """	  </TileSets>
	</TileMap>
	"""
		return s
			
	# -------------------------------------------------------------------------
	def generate_googlemaps(self):
		"""
		Template for googlemaps.html implementing Overlay of tiles for 'mercator' profile.
		It returns filled string. Expected variables:
		title, googlemapskey, north, south, east, west, minzoom, maxzoom, tilesize, tileformat, publishurl
		"""
		args = {}
		args['title'] = self.options.title
		args['googlemapskey'] = self.options.googlekey
		args['south'], args['west'], args['north'], args['east'] = self.swne
		args['minzoom'] = self.tminz
		args['maxzoom'] = self.tmaxz
		args['tilesize'] = self.tilesize
		args['tileformat'] = format_extension[self.image_output.format]
		args['publishurl'] = "" if self.options.url is None else self.options.url
		args['copyright'] = self.options.copyright

		s = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
			<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml"> 
			  <head>
			    <title>%(title)s</title>
			    <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
			    <meta http-equiv='imagetoolbar' content='no'/>
			    <style type="text/css"> v\:* {behavior:url(#default#VML);}
			        html, body { overflow: hidden; padding: 0; height: 100%%; width: 100%%; font-family: 'Lucida Grande',Geneva,Arial,Verdana,sans-serif; }
			        body { margin: 10px; background: #fff; }
			        h1 { margin: 0; padding: 6px; border:0; font-size: 20pt; }
			        #header { height: 43px; padding: 0; background-color: #eee; border: 1px solid #888; }
			        #subheader { height: 12px; text-align: right; font-size: 10px; color: #555;}
			        #map { height: 95%%; border: 1px solid #888; }
			    </style>
			    <script src='http://maps.google.com/maps?file=api&amp;v=2&amp;key=%(googlemapskey)s' type='text/javascript'></script>
			    <script type="text/javascript">
			    //<![CDATA[

			    /*
			     * Constants for given map
			     * TODO: read it from tilemapresource.xml
			     */

			    var mapBounds = new GLatLngBounds(new GLatLng(%(south)s, %(west)s), new GLatLng(%(north)s, %(east)s));
			    var mapMinZoom = %(minzoom)s;
			    var mapMaxZoom = %(maxzoom)s;

			    var opacity = 0.75;
			    var map;
			    var ge;
			    var hybridOverlay;

			    /*
			     * Create a Custom Opacity GControl
			     * http://www.maptiler.org/google-maps-overlay-opacity-control/
			     */

			    var CTransparencyLENGTH = 58; 
			    // maximum width that the knob can move (slide width minus knob width)

			    function CTransparencyControl( overlay ) {
			        this.overlay = overlay;
			        this.opacity = overlay.getTileLayer().getOpacity();
			    }
			    CTransparencyControl.prototype = new GControl();

			    // This function positions the slider to match the specified opacity
			    CTransparencyControl.prototype.setSlider = function(pos) {
			        var left = Math.round((CTransparencyLENGTH*pos));
			        this.slide.left = left;
			        this.knob.style.left = left+"px";
			        this.knob.style.top = "0px";
			    }

			    // This function reads the slider and sets the overlay opacity level
			    CTransparencyControl.prototype.setOpacity = function() {
				    // set the global variable
			        opacity = this.slide.left/CTransparencyLENGTH;
			        this.map.clearOverlays();
			        this.map.addOverlay(this.overlay, { zPriority: 0 });
			        if (this.map.getCurrentMapType() == G_HYBRID_MAP) {
			            this.map.addOverlay(hybridOverlay);
			        }
			    }

			    // This gets called by the API when addControl(new CTransparencyControl())
			    CTransparencyControl.prototype.initialize = function(map) {
			        var that=this;
			        this.map = map;

			        // Is this MSIE, if so we need to use AlphaImageLoader
			        var agent = navigator.userAgent.toLowerCase();
			        if ((agent.indexOf("msie") > -1) && (agent.indexOf("opera") < 1)){this.ie = true} else {this.ie = false}

			        // create the background graphic as a <div> containing an image
			        var container = document.createElement("div");
			        container.style.width="70px";
			        container.style.height="21px";

			        // Handle transparent PNG files in MSIE
			        if (this.ie) {
			          var loader = "filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src='http://download.osgeo.org/livedvd/data/mapslicer/opacity-slider.png', sizingMethod='crop');";
			          container.innerHTML = '<div style="height:21px; width:70px; ' +loader+ '" ></div>';
			        } else {
			          container.innerHTML = '<div style="height:21px; width:70px; background-image: url(http://download.osgeo.org/livedvd/data/mapslicer/opacity-slider.png)" ></div>';
			        }

			        // create the knob as a GDraggableObject
			        // Handle transparent PNG files in MSIE
			        if (this.ie) {
			          var loader = "progid:DXImageTransform.Microsoft.AlphaImageLoader(src='http://download.osgeo.org/livedvd/data/mapslicer/opacity-slider.png', sizingMethod='crop');";
			          this.knob = document.createElement("div"); 
			          this.knob.style.height="21px";
			          this.knob.style.width="13px";
				  this.knob.style.overflow="hidden";
			          this.knob_img = document.createElement("div"); 
			          this.knob_img.style.height="21px";
			          this.knob_img.style.width="83px";
			          this.knob_img.style.filter=loader;
				  this.knob_img.style.position="relative";
				  this.knob_img.style.left="-70px";
			          this.knob.appendChild(this.knob_img);
			        } else {
			          this.knob = document.createElement("div"); 
			          this.knob.style.height="21px";
			          this.knob.style.width="13px";
			          this.knob.style.backgroundImage="url(http://download.osgeo.org/livedvd/data/mapslicer/opacity-slider.png)";
			          this.knob.style.backgroundPosition="-70px 0px";
			        }
			        container.appendChild(this.knob);
			        this.slide=new GDraggableObject(this.knob, {container:container});
			        this.slide.setDraggableCursor('pointer');
			        this.slide.setDraggingCursor('pointer');
			        this.container = container;

			        // attach the control to the map
			        map.getContainer().appendChild(container);

			        // init slider
			        this.setSlider(this.opacity);

			        // Listen for the slider being moved and set the opacity
			        GEvent.addListener(this.slide, "dragend", function() {that.setOpacity()});
			        //GEvent.addListener(this.container, "click", function( x, y ) { alert(x, y) });

			        return container;
			      }

			      // Set the default position for the control
			      CTransparencyControl.prototype.getDefaultPosition = function() {
			        return new GControlPosition(G_ANCHOR_TOP_RIGHT, new GSize(7, 47));
			      }

			    /*
			     * Full-screen Window Resize
			     */

			    function getWindowHeight() {
			        if (self.innerHeight) return self.innerHeight;
			        if (document.documentElement && document.documentElement.clientHeight)
			            return document.documentElement.clientHeight;
			        if (document.body) return document.body.clientHeight;
			        return 0;
			    }

			    function getWindowWidth() {
			        if (self.innerWidth) return self.innerWidth;
			        if (document.documentElement && document.documentElement.clientWidth)
			            return document.documentElement.clientWidth;
			        if (document.body) return document.body.clientWidth;
			        return 0;
			    }

			    function resize() {  
			        var map = document.getElementById("map");  
			        var header = document.getElementById("header");  
			        var subheader = document.getElementById("subheader");  
			        map.style.height = (getWindowHeight()-80) + "px";
			        map.style.width = (getWindowWidth()-20) + "px";
			        header.style.width = (getWindowWidth()-20) + "px";
			        subheader.style.width = (getWindowWidth()-20) + "px";
			        // map.checkResize();
			    } 


			    /*
			     * Main load function:
			     */

			    function load() {

			       if (GBrowserIsCompatible()) {

			          // Bug in the Google Maps: Copyright for Overlay is not correctly displayed
			          var gcr = GMapType.prototype.getCopyrights;
			          GMapType.prototype.getCopyrights = function(bounds,zoom) {
			              return ["%(copyright)s"].concat(gcr.call(this,bounds,zoom));
			          }

			          map = new GMap2( document.getElementById("map"), { backgroundColor: '#fff' } );

			          map.addMapType(G_PHYSICAL_MAP);
			          map.setMapType(G_PHYSICAL_MAP);

			          map.setCenter( mapBounds.getCenter(), map.getBoundsZoomLevel( mapBounds ));

			          hybridOverlay = new GTileLayerOverlay( G_HYBRID_MAP.getTileLayers()[1] );
			          GEvent.addListener(map, "maptypechanged", function() {
			            if (map.getCurrentMapType() == G_HYBRID_MAP) {
			                map.addOverlay(hybridOverlay);""" % args
		if self.kml:
			s += """
			            } else if (map.getCurrentMapType() == G_SATELLITE_3D_MAP) {
			                var url = document.location.toString();
			                if (url.substr(0,4) != 'http') alert('You have to upload the tiles to a webserver to see the overlay in Google Earth Plugin');
			                if (!ge) map.getEarthInstance(getEarthInstanceCB);"""
		s += """
			            } else {
			               map.removeOverlay(hybridOverlay);
			            }
			          } );

			          var tilelayer = new GTileLayer(GCopyrightCollection(''), mapMinZoom, mapMaxZoom);
			          var mercator = new GMercatorProjection(mapMaxZoom+1);
			          tilelayer.getTileUrl = function(tile,zoom) {
			              if ((zoom < mapMinZoom) || (zoom > mapMaxZoom)) {
			                  return "http://download.osgeo.org/livedvd/data/mapslicer/none.png";
			              } 
			              var ymax = 1 << zoom;
			              var y = ymax - tile.y -1;
			              var tileBounds = new GLatLngBounds(
			                  mercator.fromPixelToLatLng( new GPoint( (tile.x)*256, (tile.y+1)*256 ) , zoom ),
			                  mercator.fromPixelToLatLng( new GPoint( (tile.x+1)*256, (tile.y)*256 ) , zoom )
			              );
			              if (mapBounds.intersects(tileBounds)) {
			                  return zoom+"/"+tile.x+"/"+y+".%(tileformat)s";
			              } else {
			                  return "http://download.osgeo.org/livedvd/data/mapslicer/none.png";
			              }
			          }
			          // IE 7-: support for PNG alpha channel
			          // Unfortunately, the opacity for whole overlay is then not changeable, either or...
			          tilelayer.isPng = function() { return true;};
			          tilelayer.getOpacity = function() { return opacity; }

			          overlay = new GTileLayerOverlay( tilelayer );
			          map.addOverlay(overlay);

			          map.addControl(new GLargeMapControl3D());
			          map.addControl(new GHierarchicalMapTypeControl());
			          map.addControl(new CTransparencyControl( overlay ));
		""" % args
		if self.kml:
			s += """
			          map.addMapType(G_SATELLITE_3D_MAP);
		"""
		s += """

			          map.enableContinuousZoom();
			          map.enableScrollWheelZoom();

			          map.setMapType(G_HYBRID_MAP);
			       }
			       resize();
			    }
		"""
		if self.kml:
			s += """
			    function getEarthInstanceCB(object) {
			       ge = object;
			       var url = document.location.toString();
			       var newurl = url.substr(0,url.lastIndexOf('/'))+'/doc.kml';
			       if (ge) {
			           var link = ge.createLink("");
			           if ("%(publishurl)s") { link.setHref("%(publishurl)s/doc.kml") }
			           else { link.setHref(newurl) };
			           var networkLink = ge.createNetworkLink("");
			           networkLink.set(link, false, false);
			           ge.getFeatures().appendChild(networkLink);
			       } else {
			           // alert("Initialization of the Google Earth Plugin failed. You can still open the KML file in normal Google Earth.");
			           // window.location = newurl; // JavaScript redirect to the URL of KML
			       }
			    }
		""" % args
		s += """
			    onresize=function(){ resize(); };

			    //]]>
			    </script>
			  </head>
			  <body onload="load()">
			      <div id="header"><h1>%(title)s</h1></div>
                  <div id="subheader">Generated by <a href="https://wiki.osgeo.org/wiki/MapSlicer">MapSlicer</a>/<a href="http://www.gdal.org/">GDAL</a> &amp; <a href="http://www.osgeo.org/">OSGeo</a></div>
			       <div id="map"></div>
			  </body>
			</html>
		""" % args

		return s


	# -------------------------------------------------------------------------
	def generate_openlayers( self ):
		"""
		Template for openlayers.html implementing overlay of available Spherical Mercator layers.

		It returns filled string. Expected variables:
		title, googlemapskey, yahooappid, north, south, east, west, minzoom, maxzoom, tilesize, tileformat, publishurl
		"""

		args = {}
		args['title'] = self.options.title
		args['googlemapskey'] = self.options.googlekey
		args['yahooappid'] = self.options.yahookey
		args['south'], args['west'], args['north'], args['east'] = self.swne
		args['minzoom'] = self.tminz
		args['maxzoom'] = self.tmaxz
		args['tilesize'] = self.tilesize
		args['tileformat'] = format_extension[self.image_output.format]
		if self.image_output.format == "PNG":
			args['has_alpha'] = 'true'
		else:
			args['has_alpha'] = 'false'
		args['publishurl'] = "" if self.options.url is None else self.options.url
		args['copyright'] = self.options.copyright
		if self.options.profile in ('raster', 'gearth'):
			args['rasterzoomlevels'] = self.tmaxz+1
			args['rastermaxresolution'] = 2**(self.nativezoom) * self.out_gt[1]

		s = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
		<html xmlns="http://www.w3.org/1999/xhtml>"
		  <head>
		    <title>%(title)s</title>
		    <meta http-equiv='imagetoolbar' content='no'/>
		    <style type="text/css"> v\:* {behavior:url(#default#VML);}
		        html, body { overflow: hidden; padding: 0; height: 100%%; width: 100%%; font-family: 'Lucida Grande',Geneva,Arial,Verdana,sans-serif; }
		        body { margin: 10px; background: #fff; }
		        h1 { margin: 0; padding: 6px; border:0; font-size: 20pt; }
		        #header { height: 43px; padding: 0; background-color: #eee; border: 1px solid #888; }
		        #subheader { height: 12px; text-align: right; font-size: 10px; color: #555;}
		        #map { height: 95%%; border: 1px solid #888; }
		    </style>""" % args
		
		if self.options.profile == 'mercator':
			s += """
		    <script src='http://dev.virtualearth.net/mapcontrol/mapcontrol.ashx?v=6.1'></script>
		    <script src='http://maps.google.com/maps?file=api&amp;v=2&amp;key=%(googlemapskey)s' type='text/javascript'></script>
		    <script src="http://api.maps.yahoo.com/ajaxymap?v=3.0&amp;appid=%(yahooappid)s"></script>""" % args

		s += """
		    <script src="http://www.openlayers.org/api/2.7/OpenLayers.js" type="text/javascript"></script>
		    <script type="text/javascript">
		        var map;
			    var mapBounds = new OpenLayers.Bounds( %(west)s, %(south)s, %(east)s, %(north)s);
			    var mapMinZoom = %(minzoom)s;
			    var mapMaxZoom = %(maxzoom)s;

		        // avoid pink tiles
		        OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;
		        OpenLayers.Util.onImageLoadErrorColor = "transparent";

		        function init(){""" % args

		if self.options.profile == 'mercator':
			s += """
	            var options = {
	                controls: [],
	                projection: new OpenLayers.Projection("EPSG:3857"),
	                displayProjection: new OpenLayers.Projection("EPSG:4326"),
	                units: "m",
	                maxResolution: 156543.0339,
	                maxExtent: new OpenLayers.Bounds(-20037508, -20037508, 20037508, 20037508.34)
		            };
	            map = new OpenLayers.Map('map', options);

	            // create Google Mercator layers
	            var gmap = new OpenLayers.Layer.Google("Google Streets",
					{ sphericalMercator: true, numZoomLevels: 20} );
	            var gsat = new OpenLayers.Layer.Google("Google Satellite",
					{type: G_SATELLITE_MAP, sphericalMercator: true, numZoomLevels: 20} );
	            var ghyb = new OpenLayers.Layer.Google("Google Hybrid",
					{type: G_HYBRID_MAP, sphericalMercator: true, numZoomLevels: 20});
	            var gter = new OpenLayers.Layer.Google("Google Terrain",
					{type: G_PHYSICAL_MAP, sphericalMercator: true, numZoomLevels: 20 });

	            // create Virtual Earth layers
				OpenLayers.Layer.VirtualEarth.prototype.MAX_ZOOM_LEVEL=19;
				OpenLayers.Layer.VirtualEarth.prototype.RESOLUTIONS=OpenLayers.Layer.Google.prototype.RESOLUTIONS
	            var veroad = new OpenLayers.Layer.VirtualEarth("Virtual Earth Roads",
					{'type': VEMapStyle.Road, 'sphericalMercator': true, numZoomLevels: 20});
	            var veaer = new OpenLayers.Layer.VirtualEarth("Virtual Earth Aerial",
					{'type': VEMapStyle.Aerial, 'sphericalMercator': true, numZoomLevels: 20 });
	            var vehyb = new OpenLayers.Layer.VirtualEarth("Virtual Earth Hybrid",
	                {'type': VEMapStyle.Hybrid, 'sphericalMercator': true});

	            // create Yahoo layer
	            var yahoo = new OpenLayers.Layer.Yahoo("Yahoo Street",
	                {'sphericalMercator': true});
	            var yahoosat = new OpenLayers.Layer.Yahoo("Yahoo Satellite",
	                {'type': YAHOO_MAP_SAT, 'sphericalMercator': true});
	            var yahoohyb = new OpenLayers.Layer.Yahoo("Yahoo Hybrid",
	                {'type': YAHOO_MAP_HYB, 'sphericalMercator': true});

	            // create OSM/OAM layer
	            var osm = new OpenLayers.Layer.TMS( "OpenStreetMap",
	                "http://tile.openstreetmap.org/",
	                { type: 'png', getURL: osm_getTileURL, displayOutsideMaxExtent: true, 
					  attribution: '<a href="http://www.openstreetmap.org/">OpenStreetMap</a>'} );
	            var oam = new OpenLayers.Layer.TMS( "OpenAerialMap",
	                "http://tile.openaerialmap.org/tiles/1.0.0/openaerialmap-900913/",
	                { type: 'png', getURL: osm_getTileURL } );

	            // create TMS Overlay layer
	            var tmsoverlay = new OpenLayers.Layer.TMS( "TMS Overlay", "",
	                {   // url: '', serviceVersion: '.', layername: '.',
						type: '%(tileformat)s', getURL: overlay_getTileURL, alpha: %(has_alpha)s, 
						isBaseLayer: false
	                });
				if (OpenLayers.Util.alphaHack() == false) { tmsoverlay.setOpacity(0.7); }

	            map.addLayers([gmap, gsat, ghyb, gter, veroad, veaer, vehyb,
	                           yahoo, yahoosat, yahoohyb, osm, oam,
	                           tmsoverlay]);

	            var switcherControl = new OpenLayers.Control.LayerSwitcher();
	            map.addControl(switcherControl);
	            switcherControl.maximizeControl();
	
	            map.zoomToExtent( mapBounds.transform(map.displayProjection, map.projection ) );
			""" % args
	
		elif self.options.profile == 'geodetic':
			s += """
	            var options = {
	                controls: [],
		            projection: new OpenLayers.Projection("EPSG:4326"),
		            maxResolution: 0.703125,
		            maxExtent: new OpenLayers.Bounds(-180, -90, 180, 90)
		            };
	            map = new OpenLayers.Map('map', options);

	            layer = new OpenLayers.Layer.WMS( "Blue Marble",
	                    "http://labs.metacarta.com/wms-c/Basic.py?", {layers: 'satellite' } );
	            map.addLayer(layer);
	            wms = new OpenLayers.Layer.WMS( "VMap0",
	                    "http://labs.metacarta.com/wms-c/Basic.py?", {layers: 'basic', format: 'image/png' } );
	            map.addLayer(wms);
				
	            var tmsoverlay = new OpenLayers.Layer.TMS( "TMS Overlay", "",
	                {
	                    serviceVersion: '.', layername: '.', alpha: %(has_alpha)s,
						type: '%(tileformat)s', getURL: overlay_getTileURL,
						isBaseLayer: false
	                });
	            map.addLayer(tmsoverlay);
				if (OpenLayers.Util.alphaHack() == false) { tmsoverlay.setOpacity(0.7); }

	            var switcherControl = new OpenLayers.Control.LayerSwitcher();
	            map.addControl(switcherControl);
	            switcherControl.maximizeControl();

	            map.zoomToExtent( mapBounds );
			""" % args
			
		elif self.options.profile in ('raster', 'gearth'):
			s += """
	            var options = {
	                controls: [],
		            maxExtent: new OpenLayers.Bounds(  %(west)s, %(south)s, %(east)s, %(north)s ),
		            maxResolution: %(rastermaxresolution)f,
		            numZoomLevels: %(rasterzoomlevels)d
		            };
	            map = new OpenLayers.Map('map', options);
	
		        var layer = new OpenLayers.Layer.TMS( "TMS Layer","",
		            {  url: '', serviceVersion: '.', layername: '.', alpha: %(has_alpha)s,
						type: '%(tileformat)s', getURL: overlay_getTileURL 
					});
		        map.addLayer(layer);
				map.zoomToExtent( mapBounds );	
		""" % args


		s += """
	            map.addControl(new OpenLayers.Control.PanZoomBar());
	            map.addControl(new OpenLayers.Control.MousePosition());
	            map.addControl(new OpenLayers.Control.MouseDefaults());
	            map.addControl(new OpenLayers.Control.KeyboardDefaults());
	        }
			""" % args
		
		if self.options.profile == 'mercator':
			s += """
	        function osm_getTileURL(bounds) {
	            var res = this.map.getResolution();
	            var x = Math.round((bounds.left - this.maxExtent.left) / (res * this.tileSize.w));
	            var y = Math.round((this.maxExtent.top - bounds.top) / (res * this.tileSize.h));
	            var z = this.map.getZoom();
	            var limit = Math.pow(2, z);

	            if (y < 0 || y >= limit) {
	                return "http://download.osgeo.org/livedvd/data/mapslicer/none.png";
	            } else {
	                x = ((x %% limit) + limit) %% limit;
	                return this.url + z + "/" + x + "/" + y + "." + this.type;
	            }
	        }
	
	        function overlay_getTileURL(bounds) {
	            var res = this.map.getResolution();
	            var x = Math.round((bounds.left - this.maxExtent.left) / (res * this.tileSize.w));
	            var y = Math.round((bounds.bottom - this.tileOrigin.lat) / (res * this.tileSize.h));
	            var z = this.map.getZoom();
	            if (this.map.baseLayer.name == 'Virtual Earth Roads' || this.map.baseLayer.name == 'Virtual Earth Aerial' || this.map.baseLayer.name == 'Virtual Earth Hybrid') {
	               z = z + 1;
	            }
		        if (mapBounds.intersectsBounds( bounds ) && z >= mapMinZoom && z <= mapMaxZoom ) {
	               //console.log( this.url + z + "/" + x + "/" + y + "." + this.type);
	               return this.url + z + "/" + x + "/" + y + "." + this.type;
                } else {
                   return "http://download.osgeo.org/livedvd/data/mapslicer/none.png";
                }
	        }		
			""" % args
			
		elif self.options.profile == 'geodetic':
			s += """
	        function overlay_getTileURL(bounds) {
				bounds = this.adjustBounds(bounds);
	            var res = this.map.getResolution();
	            var x = Math.round((bounds.left - this.tileOrigin.lon) / (res * this.tileSize.w));
	            var y = Math.round((bounds.bottom - this.tileOrigin.lat) / (res * this.tileSize.h));
	            var z = this.map.getZoom();
				var path = this.serviceVersion + "/" + this.layername + "/" + z + "/" + x + "/" + y + "." + this.type;
				var url = this.url;
		        if (mapBounds.intersectsBounds( bounds ) && z >= mapMinZoom && z <= mapMaxZoom) {
	               // console.log( this.url + z + "/" + x + "/" + y + "." + this.type);
	               return this.url + z + "/" + x + "/" + y + "." + this.type;
                } else {
                   return "http://download.osgeo.org/livedvd/data/mapslicer/none.png";
                }
	        }
			""" % args
			
		elif self.options.profile in ('raster','gearth'):
			s += """
	        function overlay_getTileURL(bounds) {
	            var res = this.map.getResolution();
	            var x = Math.round((bounds.left - this.maxExtent.left) / (res * this.tileSize.w));
	            var y = Math.round((bounds.bottom - this.maxExtent.bottom) / (res * this.tileSize.h));
	            var z = this.map.getZoom();
				if (x >= 0 && y >= 0) {
		            return this.url + z + "/" + x + "/" + y + "." + this.type;				
				} else {
		        return "http://download.osgeo.org/livedvd/data/mapslicer/none.png";
				}
			}
			""" % args
		
		s += """
		   function getWindowHeight() {
		        if (self.innerHeight) return self.innerHeight;
		        if (document.documentElement && document.documentElement.clientHeight)
		            return document.documentElement.clientHeight;
		        if (document.body) return document.body.clientHeight;
			        return 0;
		    }

		    function getWindowWidth() {
			    if (self.innerWidth) return self.innerWidth;
			    if (document.documentElement && document.documentElement.clientWidth)
			        return document.documentElement.clientWidth;
			    if (document.body) return document.body.clientWidth;
			        return 0;
		    }

		    function resize() {  
			    var map = document.getElementById("map");  
			    var header = document.getElementById("header");  
			    var subheader = document.getElementById("subheader");  
			    map.style.height = (getWindowHeight()-80) + "px";
			    map.style.width = (getWindowWidth()-20) + "px";
			    header.style.width = (getWindowWidth()-20) + "px";
			    subheader.style.width = (getWindowWidth()-20) + "px";
				if (map.updateSize) { map.updateSize(); };
		    } 

		    onresize=function(){ resize(); };

		    </script>
		  </head>
		  <body onload="init()">
			<div id="header"><h1>%(title)s</h1></div>
                  <div id="subheader">Generated by <a href="https://wiki.osgeo.org/wiki/MapSlicer">MapSlicer</a>/<a href="http://www.gdal.org/">GDAL</a> &amp; <a href="http://www.osgeo.org/">OSGeo</a></div>
		    <div id="map"></div>
		    <script type="text/javascript" >resize()</script>
		  </body>
		</html>""" % args

		return s

# =============================================================================
# =============================================================================
# =============================================================================


def ImageOutput(name, out_ds, tile_size, resampling, init_dest, output_dir, verbose):

	"""Return object representing tile image output implementing given parameters."""

	resampler = Resampler(resampling)

	if name == "hybrid":
		return HybridImageOutput(out_ds, tile_size, resampler, init_dest, output_dir, verbose)

	if name == "png":
		image_format = "PNG"
	elif name == "jpeg":
		image_format = "JPEG"

	return SimpleImageOutput(out_ds, tile_size, resampler, init_dest, output_dir, verbose, [image_format])


class ImageOutputException(Exception):

	"""Raised when the tile image can't be saved to disk."""


class BaseImageOutput(object):

	"""Base class for image output.
	
	Child classes are supposed to provide two methods `write_base_tile' and
	`write_overview_tile'. These will call `create_base_tile' and `create_overview_tile'
	with arguments appropriate to their output strategy.

	When this class is instantiated with only one image format, it is stored in
	a member field `format'.
	"""

	def __init__(self, out_ds, tile_size, resampler, init_dest, output_dir, verbose, image_formats):
		self.out_ds = out_ds
		self.tile_size = tile_size
		self.resampler = resampler
		self.init_dest = init_dest
		self.output_dir = output_dir
		self.verbose = verbose
		self.image_formats = image_formats
		if len(self.image_formats) == 1:
			self.format = self.image_formats[0]

		self.mem_drv = get_gdal_driver("MEM")
		self.alpha = None
		self.alpha_filler = None

		# Get alpha band (either directly or from NODATA value)
		self.alpha_band = self.out_ds.GetRasterBand(1).GetMaskBand()
		if (self.alpha_band.GetMaskFlags() & gdal.GMF_ALPHA) or self.out_ds.RasterCount in (2, 4):
			# TODO: Better test for alpha band in the dataset
			self.data_bands_count = self.out_ds.RasterCount - 1
		else:
			self.data_bands_count = self.out_ds.RasterCount

	def write_base_tile(self, tx, ty, tz, xyzzy):

		"""Create image of a base level tile and write it to disk."""

		data_bands = range(1, self.data_bands_count+1)
		data = self.out_ds.ReadRaster(xyzzy.rx, xyzzy.ry, xyzzy.rxsize, xyzzy.rysize,
									  xyzzy.wxsize, xyzzy.wysize, band_list=data_bands)

		image_format = self.get_base_tile_format(tx, ty, tz, xyzzy)

		if image_format is None:
			return
		else:
			num_bands = self.get_num_bands(image_format)

		if self.verbose:
			print "\tReadRaster Extent: ", (xyzzy.rx, xyzzy.ry, xyzzy.rxsize, xyzzy.rysize),
			print (xyzzy.wx, xyzzy.wy, xyzzy.wxsize, xyzzy.wysize)

		dstile = self.mem_drv.Create('', self.tile_size, self.tile_size, num_bands)

		path = self.get_full_path(tx, ty, tz, format_extension[image_format])

		# Query is in 'nearest neighbour' but can be bigger in then the tilesize
		# We scale down the query to the tilesize by supplied algorithm.
		if self.tile_size == xyzzy.querysize:
			self.fill_init_dest(dstile)

			# Use the ReadRaster result directly in tiles ('nearest neighbour' query) 
			dstile.WriteRaster(xyzzy.wx, xyzzy.wy, xyzzy.wxsize, xyzzy.wysize, data, band_list=data_bands)
			if image_format == "PNG":
				dstile.WriteRaster(xyzzy.wx, xyzzy.wy, xyzzy.wxsize, xyzzy.wysize, self.alpha, band_list=[num_bands])

			gdal_write(path, dstile, image_format)

			# Note: For source drivers based on WaveLet compression (JPEG2000, ECW, MrSID)
			# the ReadRaster function returns high-quality raster (not ugly nearest neighbour)
			# TODO: Use directly 'near' for WaveLet files
		else:
			# Big ReadRaster query in memory scaled to the tilesize - all but 'near' algo
			dsquery = self.mem_drv.Create('', xyzzy.querysize, xyzzy.querysize, num_bands)
			self.fill_init_dest(dsquery)

			dsquery.WriteRaster(xyzzy.wx, xyzzy.wy, xyzzy.wxsize, xyzzy.wysize, data, band_list=data_bands)
			if image_format == "PNG":
				dsquery.WriteRaster(xyzzy.wx, xyzzy.wy, xyzzy.wxsize, xyzzy.wysize, self.alpha, band_list=[num_bands])

			self.resampler(path, dsquery, dstile, image_format)

		self.alpha = None

	def write_overview_tile(self, tx, ty, tz):

		"""Create image of a overview level tile and write it to disk."""

		image_format = self.get_overview_tile_format(tx, ty, tz)

		if image_format is None:
			return
		else:
			num_bands = self.get_num_bands(image_format)

		dsquery = self.mem_drv.Create('', 2*self.tile_size, 2*self.tile_size, num_bands)
		self.fill_init_dest(dsquery)

		if self.verbose:
			print "\tBuild from zoom", tz+1," tiles:", (2*tx, 2*ty), (2*tx+1, 2*ty),(2*tx, 2*ty+1), (2*tx+1, 2*ty+1)

		for cx, cy, child_image_format in self.iter_children(tx, ty, tz):
			if (ty==0 and cy==1) or (ty!=0 and (cy % (2*ty)) != 0):
				tileposy = 0
			else:
				tileposy = self.tile_size
			if tx:
				tileposx = cx % (2*tx) * self.tile_size
			elif tx==0 and cx==1:
				tileposx = self.tile_size
			else:
				tileposx = 0

			path = self.get_full_path(cx, cy, tz+1, format_extension[child_image_format])
			dsquerytile = gdal.Open(path, gdal.GA_ReadOnly)

			dsquery.WriteRaster(tileposx, tileposy, self.tile_size, self.tile_size,
				dsquerytile.ReadRaster(0, 0, self.tile_size, self.tile_size),
				band_list=range(1, dsquerytile.RasterCount+1))

			if image_format == "PNG" and dsquerytile.RasterCount != num_bands:
				dsquery.WriteRaster(tileposx, tileposy, self.tile_size, self.tile_size,
					self.get_alpha_filler(), band_list=[num_bands])

		dstile = self.mem_drv.Create('', self.tile_size, self.tile_size, num_bands)
		path = self.get_full_path(tx, ty, tz, format_extension[image_format])
		self.resampler(path, dsquery, dstile, image_format)

	def iter_children(self, tx, ty, tz):
		"""Generate all children of the given tile produced on the lower level."""
		for y in range(2*ty, 2*ty + 2):
			for x in range(2*tx, 2*tx + 2):
				image_format = self.try_to_use_existing_tile(x, y, tz+1)
				if image_format is not None:
					yield x, y, image_format

	def read_alpha(self, xyzzy):
		self.alpha = self.alpha_band.ReadRaster(xyzzy.rx, xyzzy.ry, xyzzy.rxsize, xyzzy.rysize, xyzzy.wxsize, xyzzy.wysize)

	def fill_init_dest(self, image):
		if self.init_dest is not None:
			for i,v in enumerate(self.init_dest[:image.RasterCount]):
				image.GetRasterBand(i+1).Fill(v)

	def get_num_bands(self, image_format):
		if image_format == "JPEG":
			return self.data_bands_count
		else:
			return self.data_bands_count + 1

	def get_alpha_filler(self):
		if self.alpha_filler is None:
			self.alpha_filler = "\xff" * (self.tile_size * self.tile_size)
		return self.alpha_filler

	def try_to_use_existing_tile(self, tx, ty, tz):
		"""Return image format of the tile if it exists already on disk."""
		for image_format in self.image_formats:
			if os.path.exists(self.get_full_path(tx, ty, tz, format_extension[image_format])):
				return image_format
		return None

	def tile_exists(self, tx, ty, tz):
		return self.try_to_use_existing_tile(tx, ty, tz) != None

	def get_full_path(self, tx, ty, tz, extension):
		return os.path.join(self.output_dir, get_tile_filename(tx, ty, tz, extension))


class SimpleImageOutput(BaseImageOutput):

	"""Image output using only one image format."""

	def get_base_tile_format(self, tx, ty, tz, xyzzy):
		if self.format == "PNG":
			self.read_alpha(xyzzy)

		return self.format

	def get_overview_tile_format(self, tx, ty, tz):
		return self.format


class HybridImageOutput(BaseImageOutput):

	"""Image output which skips fully transparent tiles, saves the fully opaque
	as JPEG and the rest as PNG.
	"""

	def __init__(self, out_ds, tile_size, resampler, init_dest, output_dir, verbose):
		BaseImageOutput.__init__(self, out_ds, tile_size, resampler, init_dest, output_dir, verbose, ["JPEG", "PNG"])

		img = self.mem_drv.Create("", self.tile_size, self.tile_size, 1)
		rb = img.GetRasterBand(1)
		rb.Fill(0)
		self.transparent_checksum = rb.Checksum(0, 0, self.tile_size, self.tile_size)
		rb.Fill(255)
		self.opaque_checksum = rb.Checksum(0, 0, self.tile_size, self.tile_size)

	def get_base_tile_format(self, tx, ty, tz, xyzzy):
		if xyzzy.rxsize == self.tile_size and xyzzy.rysize == self.tile_size:
			c = self.alpha_band.Checksum(xyzzy.rx, xyzzy.ry, self.tile_size, self.tile_size)

			if c == self.transparent_checksum:
				if self.verbose:
					print "\tTile generation skipped because it is fully transparent"
				return None
			elif c == self.opaque_checksum:
				image_format = "JPEG"
			else:
				image_format = "PNG"
				self.read_alpha(xyzzy)
		else:
			self.read_alpha(xyzzy)
			transparent, opaque = self.transparent_or_opaque(self.alpha)

			if transparent:
				if self.verbose:
					print "\tTile generation skipped because it is fully transparent"
				return None
			elif opaque:
				image_format = "JPEG"
			else:
				image_format = "PNG"

		if self.verbose:
			print "\tSaving tile in %s format" % image_format

		return image_format

	def get_overview_tile_format(self, tx, ty, tz):
		children = list(self.iter_children(tx, ty, tz))

		if len(children) == 0:
			if self.verbose:
				print "\tTile generation skipped because it is fully transparent"
			return None

		if any(image_format == "PNG" for x, y, image_format in children) or len(children) < 4:
			image_format = "PNG"
		else:
			image_format = "JPEG"

		if self.verbose:
			print "\tSaving tile in %s format" % image_format

		return image_format

	def transparent_or_opaque(self, alpha):
		transparent = opaque = True
		for c in alpha:
			transparent = transparent and c == '\x00'
			opaque = opaque and c == '\xff'
		assert not (transparent and opaque)
		return transparent, opaque


def Resampler(name):

	"""Return a function performing given resampling algorithm."""

	def resample_average(path, dsquery, dstile, image_format):
		for i in range(1, dstile.RasterCount+1):
			res = gdal.RegenerateOverview(dsquery.GetRasterBand(i),	dstile.GetRasterBand(i), "average")
			if res != 0:
			    raise ImageOutputException("RegenerateOverview() failed with error %d" % res)

		gdal_write(path, dstile, image_format)

	def resample_antialias(path, dsquery, dstile, image_format):
		querysize = dsquery.RasterXSize
		tilesize = dstile.RasterXSize

		array = numpy.zeros((querysize, querysize, 4), numpy.uint8)
		for i in range(dstile.RasterCount):
			array[:,:,i] = gdalarray.BandReadAsArray(dsquery.GetRasterBand(i+1), 0, 0, querysize, querysize)
		im = Image.fromarray(array, 'RGBA') # Always four bands
		im1 = im.resize((tilesize,tilesize), Image.ANTIALIAS)

		if os.path.exists(path):
			im0 = Image.open(path)
			im1 = Image.composite(im1, im0, im1)

		ensure_dir_exists(path)

		if image_format == "JPEG":
			im1.save(path, image_format, quality=jpeg_quality)
		else:
			im1.save(path, image_format)


	if name == "average":
		return resample_average
	elif name == "antialias":
		return resample_antialias

	resampling_methods = {
		"near"        : gdal.GRA_NearestNeighbour,
		"bilinear"    : gdal.GRA_Bilinear,
		"cubic"       : gdal.GRA_Cubic,
		"cubicspline" : gdal.GRA_CubicSpline,
		"lanczos"     : gdal.GRA_Lanczos
	}

	resampling_method = resampling_methods[name]

	def resample_gdal(path, dsquery, dstile, image_format):
		querysize = dsquery.RasterXSize
		tilesize = dstile.RasterXSize

		dsquery.SetGeoTransform( (0.0, tilesize / float(querysize), 0.0, 0.0, 0.0, tilesize / float(querysize)) )
		dstile.SetGeoTransform( (0.0, 1.0, 0.0, 0.0, 0.0, 1.0) )

		res = gdal.ReprojectImage(dsquery, dstile, None, None, resampling_method)
		if res != 0:
		    raise ImageOutputException("ReprojectImage() failed with error %d" % res)

		gdal_write(path, dstile, image_format)

	return resample_gdal


def gdal_write(path, dstile, image_format):
	ensure_dir_exists(path)
	driver = get_gdal_driver(image_format)

	if image_format == "JPEG":
		driver.CreateCopy(path, dstile, strict=0, options=jpeg_gdal_options)
	else:
		driver.CreateCopy(path, dstile, strict=0)


def get_gdal_driver(name):
	driver = gdal.GetDriverByName(name)
	if driver is None:
		raise Exception("The '%s' driver was not found, is it available in this GDAL build?" % name)
	else:
		return driver


def get_tile_filename(tx, ty, tz, extension):
	return os.path.join(str(tz), str(tx), "%s.%s" % (ty, extension))


def ensure_dir_exists(path):
	dirname = os.path.dirname(path)
	if not os.path.exists(dirname):
		os.makedirs(dirname)


class Xyzzy(object):

	"""Collection of coordinates describing what to read where for the given tile at the base level."""

	def __init__(self, querysize, rx, ry, rxsize, rysize, wx, wy, wxsize, wysize):
		self.querysize = querysize
		self.rx = rx
		self.ry = ry
		self.rxsize = rxsize
		self.rysize = rysize
		self.wx = wx
		self.wy = wy
		self.wxsize = wxsize
		self.wysize = wysize

# ------------------------------------------------
# Functions for calculating KML <LookAt> tag:

def angular_distance(lng1, lat1, lng2, lat2):
	"""
	Haversine formula on sphere - for higher precission on ellipsoid use the Vincenty formula
	http://www.movable-type.co.uk/scripts/latlong.html
	"""

	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)

	d_phi = math.radians(lat2 - lat1)
	d_lmd = math.radians(lng2 - lng1)

	A = math.pow(math.sin(d_phi / 2), 2) + \
		math.cos(phi1) * math.cos(phi2) * \
		math.pow(math.sin(d_lmd / 2), 2)

	return 2 * math.atan2(math.sqrt(A), math.sqrt(1 - A))

def computeFitLookAt(minlng, minlat, maxlng, maxlat):
	"Ported from http://code.google.com/p/earth-api-samples/source/browse/trunk/lib/ge-poly-fit-hack.js"

	DEGREES = math.pi / 180.0
	EARTH_RADIUS = 6378137

	viewrange = 0.0
	center = [ minlng+(maxlng-minlng)/2.0, minlat+(maxlat-minlat)/2.0 ]

	lngSpan = EARTH_RADIUS * angular_distance(center[0], minlat, center[0], maxlat)
	latSpan = EARTH_RADIUS * angular_distance(minlng, center[1], maxlng, center[1])

	aspectRatio = 1.0
	PAD_FACTOR = 1.5 # add 50% to the computed range for padding

	aspectUse = max(aspectRatio, min(1.0, lngSpan / latSpan))
	alpha = (45.0 / (aspectUse + 0.4) - 2.0) * DEGREES # computed experimentally

	# create LookAt using distance formula
	if (lngSpan > latSpan): # polygon is wide
		beta = min(90 * DEGREES, alpha + lngSpan / 2 / EARTH_RADIUS)
	else: # polygon is taller
		beta = min(90 * DEGREES, alpha + latSpan / 2 / EARTH_RADIUS)

	viewrange = PAD_FACTOR * EARTH_RADIUS * (math.sin(beta) * \
		math.sqrt(1 / math.pow(math.tan(alpha),2) + 1) - 1)

	return center[0], center[1], viewrange

# =============================================================================


if __name__=='__main__':
	argv = gdal.GeneralCmdLineProcessor( sys.argv )
	if argv:
		gdal2tiles = GDAL2Tiles( argv[1:], gdalcache=128*1024*1024 )
		gdal2tiles.process()
