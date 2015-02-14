#!/usr/bin/env python

from osgeo import gdal
from osgeo import osr
import tempfile
import os
import preprocess

#TODO: GetText
from config import _

gdal.AllRegister()
vrt_drv = gdal.GetDriverByName( 'VRT' )

palettecolors = ['Red','Green','Blue','Alpha']
reference = osr.SpatialReference()


class PreprocessError(Exception):

	"""To distinguish errors from exceptions in this module."""


def singlefile(filename, bbox = None):
	"Returns [visible-filename, visible-georeference, realfilename, geotransform, xsize, ysize, srs]"
	
	osr.DontUseExceptions()
	realfilename = filename
	georeference = ""
	geotransform = None
	srs = ""
	
	in_ds = gdal.Open( filename, gdal.GA_ReadOnly)
	if not in_ds:
		# Note: GDAL prints the ERROR message too
		raise PreprocessError(_("It is not possible to open the input file '%s'.") % filename)

	xsize = in_ds.RasterXSize
	ysize = in_ds.RasterYSize
	bands = in_ds.RasterCount
	geotransform = in_ds.GetGeoTransform()
	srs = in_ds.GetProjection()

	if bbox:
		# nsew = uly lry lrx ulx 
		# TODO: set geotransform from [ulx, uly, lrx, lry] + xsize, ysize
		geotransform = [0.0,0.0,0.0,0.0,0.0,0.0]
		
		if len(bbox) > 4: # world file - affine transformation
			geotransform[1] = bbox[0] # width of pixel
			geotransform[4] = bbox[1] # rotational coefficient, zero for north up images.
			geotransform[2] = bbox[2] # rotational coefficient, zero for north up images.
			geotransform[5] = bbox[3] # height of pixel (but negative)
			geotransform[0] = bbox[4] - 0.5*bbox[0] - 0.5*bbox[2] # x offset to center of top left pixel.
			geotransform[3] = bbox[5] - 0.5*bbox[1] - 0.5*bbox[3] # y offset to center of top left pixel.
			
		else: # bounding box
			geotransform[0] = bbox[3]
			geotransform[1] = (bbox[2] - bbox[3]) / float(xsize)
			geotransform[2] = 0.0
			geotransform[3] = bbox[0]
			geotransform[4] = 0.0
			geotransform[5] = (bbox[1] - bbox[0]) / float(ysize)

		in_ds.SetGeoTransform(geotransform)

	elif in_ds.GetGCPCount() != 0:
		georeference = "GCPs"
		srs = in_ds.GetGCPProjection()
		geotransform = gdal.GCPsToGeoTransform(in_ds.GetGCPs())
		# Maybe warping before merging ? But warping before merging should use correct pixel size based on max zoom level!
		# Or merging only with affine tranformation calculated from GCPs? 
		# self.out_ds = gdal.AutoCreateWarpedVRT( self.in_ds, self.in_srs_wkt, self.out_srs.ExportToWkt() )
	if geotransform != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0) and in_ds.GetGCPCount()==0:
		georeference = " ".join(map(str, geotransform))
	
	vrtfilename = str(tempfile.mktemp(os.path.basename(filename)+'.vrt'))

	# Is it a paletted raster?
	if in_ds.GetRasterBand(1).GetRasterColorTable() and bands==1:
		# Expand rasters with palette into RGBA
		if bbox:
			preprocess.Preprocess(['','-o',vrtfilename,realfilename+'::'+":".join(map(str,bbox))])
		else:
			preprocess.Preprocess(['','-o',vrtfilename,realfilename])
		realfilename = vrtfilename
	# Did we added an new geotransform?
	elif bbox:
		# Save to an GDAL VRT (XML) file to save new geotransform
		vrt_drv.CreateCopy(vrtfilename, in_ds)
		realfilename = vrtfilename
	
	reference.ImportFromWkt(srs)
	srs = reference.ExportToPrettyWkt()
	return filename, georeference, realfilename, geotransform, xsize, ysize, srs

def SRSInput(srs):
	osr.UseExceptions()
	reference.SetFromUserInput(srs)
	return reference.ExportToPrettyWkt()
	
if __name__=='__main__':
	import sys
	if len(sys.argv) > 1:
		print singlefile(sys.argv[1])
	else:
		print "Specify a single file to preprocess"
