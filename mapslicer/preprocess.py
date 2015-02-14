#!/usr/bin/env python
#
# MapSlicer/GDAL2Tiles Preprocess module
# -------------------------------------
# Copyright (C) 2008, Klokan Petr Pridal <klokan@klokan.cz>
#
# Based on gdal_vrtmerge.py from GDAL package:
# 
# Copyright (C) 2000, Atlantis Scientific Inc. <www.atlsci.com>
# Copyright (C) 2000, Frank Warmerdam, warmerdam@pobox.com
# Copyright (C) 2005, Gabriel Ebner <ge@gabrielebner.at>
# Copyright (C) 2005, Norman Vine  <nhv@cape.com>
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
# 
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

try:
    from osgeo import gdal, osr
except ImportError:
    import gdal, osr

import sys

# =============================================================================
def names_to_fileinfos( names ):
	"""
	Translate a list of GDAL filenames, into file_info objects.

	names -- list of valid GDAL dataset names.

	Returns a list of file_info objects.  There may be less file_info objects
	than names if some of the names could not be opened as GDAL files.
	"""
	
	file_infos = []
	for name in names:
		fi = file_info()
		if fi.init_from_name(name):
			file_infos.append(fi)

	return file_infos

# *****************************************************************************
class file_info:
	"""A class holding information about a GDAL file."""

	def init_from_name(self, filename):
		"""
		Initialize file_info from filename

		filename -- Name of file to read.

		Returns 1 on success or 0 if the file can't be opened.
		"""
		namebbox = filename.split('::')
		bbox = None
		filename = namebbox[0]
		if len(namebbox) > 1:
			bbox = map(float, namebbox[1].split(':'))
		fh = gdal.Open( filename, gdal.GA_ReadOnly )
		if fh is None:
			return False

		self.filename = filename
		self.bands = fh.RasterCount
		self.xsize = fh.RasterXSize
		self.ysize = fh.RasterYSize
		self.projection = fh.GetProjection()
		self.gcpprojection = fh.GetGCPProjection()
		self.gcps = fh.GetGCPs()
		
		self.geotransform = fh.GetGeoTransform()
		if bbox:
			self.geotransform = [0.0,0.0,0.0,0.0,0.0,0.0]
			self.geotransform[0] = bbox[0]
			self.geotransform[1] = (bbox[2] - bbox[0]) / float(self.xsize)
			self.geotransform[2] = 0.0
			self.geotransform[3] = bbox[1]
			self.geotransform[4] = 0.0
			self.geotransform[5] = (bbox[3] - bbox[1]) / float(self.ysize)
		self.ulx = self.geotransform[0]
		self.uly = self.geotransform[3]
		self.lrx = self.ulx + self.geotransform[1] * self.xsize
		self.lry = self.uly + self.geotransform[5] * self.ysize

		self.band_types = [None]
		self.nodata = [None]
		self.cts = [None]
		self.color_interps = [None]
		for i in range(1, fh.RasterCount+1):
			band = fh.GetRasterBand(i)
			self.band_types.append(band.DataType)
			if band.GetNoDataValue() != None:
				self.nodata.append(band.GetNoDataValue())
			self.color_interps.append(band.GetRasterColorInterpretation())
			self.datatypename = gdal.GetDataTypeName(band.DataType)
			self.blocksizex, self.blocksizey = band.GetBlockSize()
			ct = band.GetRasterColorTable()
			if ct is not None:
				self.cts.append(ct.Clone())
				self.palette = True
			else:
				self.palette = False
				self.cts.append(None)

		return True

	def write_source(self, t_fh, t_geotransform, xsize, ysize, s_band, nodata = None):
		t_ulx = t_geotransform[0]
		t_uly = t_geotransform[3]
		t_lrx = t_geotransform[0] + xsize * t_geotransform[1]
		t_lry = t_geotransform[3] + ysize * t_geotransform[5]

		# figure out intersection region
		tgw_ulx = max(t_ulx,self.ulx)
		tgw_lrx = min(t_lrx,self.lrx)
		if t_geotransform[5] < 0:
			tgw_uly = min(t_uly,self.uly)
			tgw_lry = max(t_lry,self.lry)
		else:
			tgw_uly = max(t_uly,self.uly)
			tgw_lry = min(t_lry,self.lry)
		
		# do they even intersect?
		if tgw_ulx >= tgw_lrx:
			return 1
		if t_geotransform[5] < 0 and tgw_uly <= tgw_lry:
			return 1
		if t_geotransform[5] > 0 and tgw_uly >= tgw_lry:
			return 1
			
		# compute target window in pixel coordinates.
		tw_xoff = int((tgw_ulx - t_geotransform[0]) / t_geotransform[1] + 0.1)
		tw_yoff = int((tgw_uly - t_geotransform[3]) / t_geotransform[5] + 0.1)
		tw_xsize = int((tgw_lrx - t_geotransform[0])/t_geotransform[1] + 0.5) \
				   - tw_xoff
		tw_ysize = int((tgw_lry - t_geotransform[3])/t_geotransform[5] + 0.5) \
				   - tw_yoff

		if tw_xsize < 1 or tw_ysize < 1:
			return 1

		# Compute source window in pixel coordinates.
		sw_xoff = int((tgw_ulx - self.geotransform[0]) / self.geotransform[1])
		sw_yoff = int((tgw_uly - self.geotransform[3]) / self.geotransform[5])
		sw_xsize = int((tgw_lrx - self.geotransform[0]) \
					   / self.geotransform[1] + 0.5) - sw_xoff
		sw_ysize = int((tgw_lry - self.geotransform[3]) \
					   / self.geotransform[5] + 0.5) - sw_yoff

		if sw_xsize < 1 or sw_ysize < 1:
			return 1
	
		if self.palette or nodata:
			t_fh.write('\t\t<ComplexSource>\n')
		else:
			t_fh.write('\t\t<SimpleSource>\n')
			
		t_fh.write(('\t\t\t<SourceFilename relativeToVRT="1">%s' + 
			'</SourceFilename>\n') % self.filename)
			
		if self.palette:
			t_fh.write('\t\t\t<SourceBand>1</SourceBand>\n')
		else:
			t_fh.write('\t\t\t<SourceBand>%i</SourceBand>\n' % s_band)
		if nodata:
			t_fh.write('\t\t\t<NoData>%f</NoData>\n' % nodata[s_band])
		t_fh.write('\t\t\t<SourceProperties RasterXSize="%i" RasterYSize="%i" DataType="%s" BlockXSize="%i" BlockYSize="%i"/>\n' \
			% (self.xsize, self.ysize, self.datatypename, self.blocksizex, self.blocksizey))
		t_fh.write('\t\t\t<SrcRect xOff="%i" yOff="%i" xSize="%i" ySize="%i"/>\n' \
			% (sw_xoff, sw_yoff, sw_xsize, sw_ysize))
		t_fh.write('\t\t\t<DstRect xOff="%i" yOff="%i" xSize="%i" ySize="%i"/>\n' \
			% (tw_xoff, tw_yoff, tw_xsize, tw_ysize))
			
		if self.palette:
			t_fh.write('\t\t\t<ColorTableComponent>%i</ColorTableComponent>\n' % s_band)
		if self.palette or nodata:
			t_fh.write('\t\t</ComplexSource>\n')
		else:
			t_fh.write('\t\t</SimpleSource>\n')

# =============================================================================
def Usage():
	print 'Usage: preprocess.py [-o out_filename] [-a_srs srs] [-a_nodata nodata]'
	print '           [-ul_lr ulx uly lrx lry] input_files'

# =============================================================================

def Preprocess(argv):
	names = []
	out_file = 'out.vrt'

	ulx = None
	psize_x = None
	separate = False
	pre_init = None
	a_srs = None
	a_nodata = None

	if argv is None:
		sys.exit( 0 )

	# Parse command line arguments.
	i = 1
	while i < len(argv):
		arg = argv[i]

		if arg == '-o':
			i = i + 1
			out_file = argv[i]

		elif arg == '-a_srs':
			i = i + 1
			a_srs = argv[i]

		elif arg == '-a_nodata':
			i = i + 1
			a_nodata = argv[i]

		elif arg == '-ul_lr':
			ulx = float(argv[i+1])
			uly = float(argv[i+2])
			lrx = float(argv[i+3])
			lry = float(argv[i+4])
			i = i + 4

		elif arg[:1] == '-':
			print 'Unrecognised command option: ', arg
			Usage()
			sys.exit( 1 )

		else:
			names.append( arg )
			
		i = i + 1

	if len(names) == 0:
		print 'No input files selected.'
		Usage()
		sys.exit( 1 )

	# Collect information on all the source files.
	file_infos = names_to_fileinfos( names )

	if ulx is None:
		ulx = file_infos[0].ulx
		uly = file_infos[0].uly
		lrx = file_infos[0].lrx
		lry = file_infos[0].lry
		
		for fi in file_infos:
			ulx = min(ulx, fi.ulx)
			uly = max(uly, fi.uly)
			lrx = max(lrx, fi.lrx)
			lry = min(lry, fi.lry)

	if psize_x is None:
		psize_x = file_infos[0].geotransform[1]
		psize_y = file_infos[0].geotransform[5]
	
	projection = file_infos[0].projection
	
	for fi in file_infos:
		pass
		# MAPTILER COMMENT
		#if fi.geotransform[1] != psize_x or fi.geotransform[5] != psize_y:
		#	print "All files must have the same scale; %s does not" \
		#		% fi.filename
		#	sys.exit(1)
		
		# MAPTILER COMMENT
		#if fi.geotransform[2] != 0 or fi.geotransform[4] != 0:
		#	print "No file must be rotated/skewed; %s is.\nTODO: gdalwarp -of vrt %s %s.vrt" % (fi.filename, fi.filename, fi.filename)
		#	sys.exit(1)
			
		#TODO: During initialization create temporary files by AutoCreateWarpedVRT for those

		#if fi.projection != projection:
		#	print "All files must be in the same projection; %s is not" \
		#		% fi.filename
		#	sys.exit(1)

	# MAPTILER COMMENT
	#geotransform = (ulx, psize_x, 0.0, uly, 0.0, psize_y)
	geotransform = file_infos[0].geotransform
	
	gcpprojection = file_infos[0].gcpprojection
	gcps = file_infos[0].gcps

	xsize = int(((lrx - ulx) / geotransform[1]) + 0.5)
	ysize = int(((lry - uly) / geotransform[5]) + 0.5)

	nodata = None
	if a_nodata:
		if a_nodata.find(',') != -1:
			nodata = a_nodata.split(',')
		elif a_nodata.find(' ') != -1:
			nodata = a_nodata.split(' ')
		else:
			nodata = [a_nodata] * 5 # bands + 1 
		nodata = map(int, nodata)

	palette = False
	bands = file_infos[0].bands
	if file_infos[0].palette:
		palette = True
		if not (nodata or file_infos[0].nodata != [None]):
			# Palette without NODATA is expanded also to an extra alpha channel
			bands = 4
		else:
			# Palette with NODATA
			bands = 3
	palettecolors = ['Red','Green','Blue','Alpha']

	if a_srs:
		srs = osr.SpatialReference()
		srs.SetFromUserInput(a_srs)
		projection = srs.ExportToWkt()

	t_fh = open(out_file, 'w')

	t_fh.write('<VRTDataset rasterXSize="%i" rasterYSize="%i">\n'
		% (xsize, ysize))

	# Datasets with GCPs can't be merged without warping in advance!!!
	if len(gcps):
		t_fh.write('\t<GCPList Projection="%s">\n' % gdal.EscapeString( gcpprojection, gdal.CPLES_XML ))
		for gcp in gcps:
			t_fh.write('\t\t<GCP Id="%s" Pixel="%.4f" Line="%.4f" X="%f" Y="%f"/>\n' %
			(gcp.Id, gcp.GCPPixel, gcp.GCPLine, gcp.GCPX, gcp.GCPY))
		t_fh.write('\t</GCPList>\n')
	else:
		t_fh.write('\t<GeoTransform>%24.13f, %24.13f, %24.13f, %24.13f, %24.13f, %24.13f</GeoTransform>\n'
			% geotransform)

		if len(projection) > 0:
			t_fh.write('\t<SRS>%s</SRS>\n' % gdal.EscapeString( projection, gdal.CPLES_XML ))

	if nodata:
		nd = nodata
		t_fh.write('\t<Metadata>\n\t\t<MDI key="NODATA_VALUES">%i %i %i</MDI>\n\t</Metadata>\n' % (nd[0],nd[1],nd[2]))
	if file_infos[0].nodata != [None]:
		nd = file_infos[0].nodata
		t_fh.write('\t<Metadata>\n\t\t<MDI key="NODATA_VALUES">%i %i %i</MDI>\n\t</Metadata>\n' % (nd[0],nd[1],nd[2]))

	for band in range(1, bands+1):
		dataType = "Byte"
		# gdal.GetDataTypeName(file_infos[0].band_types[band])

		t_fh.write('\t<VRTRasterBand dataType="%s" band="%i">\n'
			% (dataType, band))
		
		if nodata:
			t_fh.write('\t\t<NoDataValue>%f</NoDataValue>\n' %
				nodata[band])
		elif file_infos[0].nodata != [None]:
			t_fh.write('\t\t<NoDataValue>%f</NoDataValue>\n' %
				file_infos[0].nodata[band])
		if palette:
			t_fh.write('\t\t<ColorInterp>%s</ColorInterp>\n' %
			palettecolors[band-1])
		else:
			t_fh.write('\t\t<ColorInterp>%s</ColorInterp>\n' %
				gdal.GetColorInterpretationName(
					file_infos[0].color_interps[band]))

		for fi in file_infos:
			fi.write_source(t_fh, geotransform, xsize, ysize, band, nodata)

		t_fh.write('\t</VRTRasterBand>\n')		

	t_fh.write('</VRTDataset>\n')

# =============================================================================
#
# Program mainline.
#

if __name__ == '__main__':
	argv = gdal.GeneralCmdLineProcessor( sys.argv )
	Preprocess(argv)
