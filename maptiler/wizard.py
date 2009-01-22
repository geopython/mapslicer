#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TODO: Cleaning the code, refactoring before 1.0 publishing

import os
import wx
import wx.html
import wx.lib.wxpTag
#import wx.animate
import webbrowser
import config

#from unicodedata import normalize, combining
#strip_diacritics = lambda text: filter(lambda i: not combining(i), normalize('NFKD', text))

class WizardHtmlWindow(wx.html.HtmlWindow):
	def __init__(self, parent, id):
		wx.html.HtmlWindow.__init__(self, parent, id, style=wx.html.HW_NO_SELECTION )
		if "gtk2" in wx.PlatformInfo:
			self.SetStandardFonts()
		self.step = 0

	def OnLinkClicked(self, linkinfo):
		webbrowser.open_new(linkinfo.GetHref())
		
	def GetActiveStep(self):
		return self.step 

	def SetStep(self, step):
		self.step = step
		if step >= len(steps):
			self.SetPage(stepfinal % (config.outputdir, config.outputdir) )
			return
		self.SetPage(steps[step])
		if step == 0:
			self.FindWindowByName('mercator').SetValue(1)
		elif step == 1:
			pass
		elif step == 2:
			if not config.srs:
				config.srs = config.files[0][6]
			if config.profile == 'raster' and not config.srs:
				config.srs = "EPSG:4326"
			self.FindWindowByName('srs').SetValue(config.srs)
		elif step == 3:
			try:
				from wxgdal2tiles import wxGDAL2Tiles
				g2t = wxGDAL2Tiles(['--profile',config.profile,'--s_srs', config.srs, str(config.files[0][2]) ])
				g2t.open_input()
				config.tminz = g2t.tminz
				config.tmaxz = g2t.tmaxz
				config.kml = g2t.kml
				del g2t
			except:
				print "!!! Exception: GDAL2Tiles initialization - for getting the default values"
			self.FindWindowByName('tminz').SetValue(config.tminz)
			self.FindWindowByName('tmaxz').SetValue(config.tmaxz)
		elif step == 4:
			filename = config.files[0][0]
			config.outputdir = os.path.join( os.path.dirname(filename),
			os.path.splitext(os.path.basename( filename ))[0] )
			self.FindWindowByName('outputdir').SetPath(config.outputdir)
		elif step == 5:
			if config.profile=='mercator':
				self.FindWindowByName('google').Enable(True)
				self.FindWindowByName('openlayers').Enable(True)
				self.FindWindowByName('kml').Enable(True)
			elif config.profile=='geodetic':
				self.FindWindowByName('google').Enable(False)
				self.FindWindowByName('openlayers').Enable(True)
				self.FindWindowByName('kml').Enable(True)
			elif config.profile=='raster':
				self.FindWindowByName('google').Enable(False)
				self.FindWindowByName('openlayers').Enable(True)
				if not config.kml:
					self.FindWindowByName('kml').Enable(False)
				
			self.FindWindowByName('google').SetValue(config.google)
			self.FindWindowByName('openlayers').SetValue(config.openlayers)
			self.FindWindowByName('kml').SetValue(config.kml)
			
		elif step == 6:
			config.title = os.path.basename( config.files[0][0] )
			self.FindWindowByName('title').SetValue(config.title)
			self.FindWindowByName('copyright').SetValue(config.copyright)
			self.FindWindowByName('googlekey').SetValue(config.googlekey)
			self.FindWindowByName('yahookey').SetValue(config.yahookey)
		
	def SaveStep(self, step):
		if step == 0:
			# Profile
			if self.FindWindowByName('mercator').GetValue():
				config.profile = 'mercator'
				config.google = True
				config.openlayers = True
				config.kml = False
			elif self.FindWindowByName('geodetic').GetValue():
				config.profile = 'geodetic'
				config.google = False
				config.openlayers = True
				config.kml = True
			elif self.FindWindowByName('raster').GetValue():
				config.profile = 'raster'
				config.google = False
				config.openlayers = True
				config.kml = False
			print config.profile
		elif step == 1:
			# Files + Nodata
			print config.files
			config.nodata = self.FindWindowByName('nodatapanel').GetColor()
			print config.nodata
		elif step == 2:
			config.oldsrs = config.srs
			config.srs = self.FindWindowByName('srs').GetValue().encode('utf-8').strip()
			config.srsformat = self.FindWindowByName('srs').GetSelection()
			print config.srs
		elif step == 3:
			config.tminz = int(self.FindWindowByName('tminz').GetValue())
			config.tmaxz = int(self.FindWindowByName('tmaxz').GetValue())
			print config.tminz
			print config.tmaxz
		elif step == 4:
			config.outputdir = self.FindWindowByName('outputdir').GetPath().encode('utf8')
			config.url = self.FindWindowByName('url').GetValue()
			if config.url == 'http://':
				config.url = ''
			print config.outputdir
			print config.url
		elif step == 5:
			config.google = self.FindWindowByName('google').GetValue()
			config.openlayers = self.FindWindowByName('openlayers').GetValue()
			config.kml = self.FindWindowByName('kml').GetValue()
			print config.google
			print config.openlayers
			print config.kml
		elif step == 6:
			config.title = self.FindWindowByName('title').GetValue().encode('utf8')
			if not config.title:
				config.title = os.path.basename( config.files[0][0] ).encode('utf8')
			config.copyright = self.FindWindowByName('copyright').GetValue().encode('utf8')
			config.googlekey = self.FindWindowByName('googlekey').GetValue().encode('utf8')
			config.yahookey = self.FindWindowByName('yahookey').GetValue().encode('utf8')
			print config.title
			print config.copyright
			print config.googlekey
			print config.yahookey
	
	def UpdateRenderProgress(self, complete):
		if self.step != len(steps) - 1:
			print "Nothing to update - progressbar not displayed"
			return
		else:
			progressbar = self.FindWindowByName('progressbar')
			progressbar.SetValue(complete)

	def UpdateRenderText(self, text):
		if self.step != len(steps) - 1:
			print "Nothing to update - progresstext not displayed"
			return
		else:
			progresstext = self.FindWindowByName('progresstext')
			progresstext.SetLabel(text)
			


step1 = """<h3>Step 1: Tile Profile</h3>
	MapTiler generates tiles for simple online publishing of maps. It offers several tile profiles - several approaches how to cut a map into small tiles.
	<p>
	<font color="#DC5309" size="large"><b>What kind of tiles would you like to generate?</b></font>
	<p>
	<font size="-1">
	<wxp module="wx" class="RadioButton" name="test">
	    <param name="label" value="Global Spherical Mercator (tiles a la Google Maps)">
	    <param name="name" value="mercator">
	</wxp>
	<blockquote>
	Tiles compatible with Google Maps, Yahoo Maps, MS Virtual Earth, OpenStreetMap, etc. Suitable for overlay mashups or mashups with new map layers compatible with existing interactive maps.
	<a href="http://www.maptiler.org/google-maps-coordinate-system-projection-epsg-900913-3785/">More info</a>.
	</blockquote>
	<wxp module="wx" class="RadioButton" name="test">
	    <param name="label" value="Global Geodetic (unprojected WGS84)">
	    <param name="name" value="geodetic">
	</wxp>
	<blockquote>
	Compatible with most existing WMS servers, with OpenLayers base map, Google Earth and other applications using WGS84 coordinates (<a href="http://www.spatialreference.org/ref/epsg/4326/">EPSG:4326</a>). 
	</blockquote>
	<wxp module="wx" class="RadioButton" name="test">
	    <param name="label" value="Image Based Tiles">
	    <param name="name" value="raster">
	</wxp>
	<blockquote>
	Tiles based on the dimensions of the picture in pixels (width and height). Result will look exactly as the original input file (no reprojection of the picture), but the tiles are for stand-alone presetation only. Georeference is not necessary. If input has georeference in WGS84 (EPSG:4326) it is possible to display it in Google Earth.
	</blockquote>
	</font>"""
	
step2 = """<h3>Step 2: Source Data Files</h3>
	Please choose raster files of the maps you would like to publish.
	<p>
	<font color="#DC5309" size="large"><b>Input raster map files:</b></font>
	<p>
	<!--
	<wxp module="wx" class="ListCtrl" name="listctrl" height="250" width="100%">
	    <param name="name" value="listctrl">
	</wxp>
	-->
	<wxp module="maptiler.widgets" class="FilePanel" name="test" height="230" width=100%>
	<param name="name" value="filepanel"></wxp>
	<p>
	<wxp module="maptiler.widgets" class="NodataPanel" name="test" height="30" width=100%>
	<param name="name" value="nodatapanel"></wxp>"""

step3 = """<h3>Step 3: Spatial Reference</h3>
	It is necessary to have exact definition of the coordinate system used for georeference of the input files, the Spatial Reference System (SRS). If this information is embedded in the input files we use it. The default is latitude and longitude in WGS84 datum without map projection (EPSG:4326).
	<p>
	<font color="#DC5309" size="large"><b>What is the Spatial Reference System used in your files?</b></font>
	<p>
	<wxp module="maptiler.widgets" class="SpatialReferencePanel" name="test" height="200" width=100%>
	<param name="name" value="srs">
	</wxp>
	<font size="-1">
	Note: More info about spatial reference is at <a href="http://help.maptiler.org/coordinates/">http://help.maptiler.org/coordinates/</a>.
	</font>"""

step4 = """<h3>Step 4: Tile Details</h3> <!-- Zoom levels, Tile Format (PNG/JPEG) & Adressing, PostProcessing -->
	In this step you should specify the details related to rendered tile pyramid.
	<!-- file format and convention for tile adressing (names of the tile files) which you would like to use. -->
	<p>
	<font color="#DC5309" size="large"><b>Zoom levels to generate:</b></font>
	<p>
	Minimal zoom: <wxp module="wx" class="SpinCtrl" name="test"><param name="name" value="tminz"></wxp> &nbsp;
	Maximal: <wxp module="wx" class="SpinCtrl" name="test"><param name="name" value="tmaxz"></wxp>
	<p>&nbsp;
	<p>
	<font size="-1">
	Note: We recommend to <a href="http://blog.klokan.cz/2008/11/png-palette-with-variable-alpha-small.html">postprocess the produced tiles by PNGNQ utility</a>.
	This step is not yet available as the GUI option same as JPEG format for tiles or <a href="http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/">native Google addressing of tiles</a>.
	</font>

	<!--
	sc = wx.SpinCtrl(self, -1, "", (30, 50))
	        sc.SetRange(1,100)
	        sc.SetValue(5)
	<p>
	<font color="#DC5309" size="large"><b>Please choose a file format</b></font>
	<p>
	File format: <wxp module="wx" class="Choice" name="test"><param name="name" value="format"></wxp>
	<wxp module="wx" class="RadioButton" name="test"><param name="name" value="raster"><param name="label" value="PNG - supports overlay transparency"></wxp>
	<wxp module="wx" class="RadioButton" name="test"><param name="name" value="raster"><param name="label" value="JPEG - smaller but without transparency"></wxp>
	<p>
	<font color="#DC5309" size="large"><b>Tile adressing:</b></font>
	<p>
	<font size="-1">
	<wxp module="wx" class="RadioButton" name="test"><param name="name" value="raster"><param name="label" value="OSGeo TMS - Tile Map Service"></wxp>
	<blockquote>
	Tile adressing used in open-source software tools. Info: <a href="http://wiki.osgeo.org/wiki/Tile_Map_Service_Specification">Tile Map Service</a>.
	</blockquote>
	<wxp module="wx" class="RadioButton" name="test"><param name="name" value="raster"><param name="label" value="Google - Native Google Adressing"></wxp>
	<blockquote>
	Native tile adressing used by Google Maps API. Info: <a href="http://code.google.com/apis/maps/documentation/overlays.html#Google_Maps_Coordinates">Google Maps Coordinates</a>
	</blockquote>
	<wxp module="wx" class="RadioButton" name="test"><param name="name" value="raster"><param name="label" value="Microsoft - QuadTree"></wxp>
	<blockquote>
	Tile adressing used in Microsoft products. Info: <a href="http://msdn.microsoft.com/en-us/library/bb259689.aspx">Virtal Earth Tile System</a>
	</blockquote>
	<wxp module="wx" class="RadioButton" name="test"><param name="name" value="raster"><param name="label" value="Zoomify"></wxp>
	<blockquote>
	Format of tiles used in popular web viewer. Info: <a href="http://www.zoomify.com">Zoomify.com</a>.
	</blockquote>
	<wxp module="wx" class="RadioButton" name="test"><param name="name" value="raster"><param name="label" value="Deep Zoom"></wxp>
	<blockquote>
	Tile format used in Deep Zoom viewers of the Microsoft SeaDragon project.
	</blockquote>
	</font>
	-->
	"""

step5 = """<h3>Step 5: Destination</h3>
Please select a directory where the generated tiles should be saved. Similarly you can specify Internet adress where will you publish the map.
<p>
<font color="#DC5309" size="large"><b>Where to save the generated tiles?</b></font>
<p>
Result directory:<br/>
<wxp module="wx" class="DirPickerCtrl" name="outputdir" width="100%" height="30"><param name="name" value="outputdir"></wxp>
<p>
<font color="#DC5309" size="large"><b>The Internet adress (URL) for publishing the map:</b></font>
<p>
Destination URL:<br/>
<wxp module="wx" class="TextCtrl" name="test" width="100%"><param name="name" value="url"><param name="value" value="http://"></wxp>
<p>
<font size="-1">
Note: You should specify the URL if you need to generate correct KML for Google Earth.
</font>"""

step6 = """<h3>Step 6: Viewers</h3>
MapTiler can generate also simple web viewers for the map presentation of the tiles. Such viewers you can use as a base for you mashups. Similarly it is possible to generate KML files for Google Earth.
<p>
<font color="#DC5309" size="large"><b>What viewers should be generated?</b></font>
<p>
<font size="-1">
<wxp module="wx" class="CheckBox" name="test"><param name="name" value="google"><param name="label" value="Google Maps"></wxp>
<blockquote>
Overlay presentation of your maps on top of standard Google Maps layers. If KML is generated then Google Earth Plugin is used as well.
</blockquote>
<wxp module="wx" class="CheckBox" name="test"><param name="name" value="openlayers"><param name="label" value="OpenLayers"></wxp>
<blockquote>
Overlay of Google Maps, Virtual Earth, Yahoo Maps, OpenStreetMap and OpenAerialMap, WMS and WFS layers and another sources available in the open-source project <a href="http://www.openlayers.org/">OpenLayers</a>.
</blockquote>
<wxp module="wx" class="CheckBox" name="test"><param name="name" value="kml"><param name="label" value="Google Earth (KML SuperOverlay)"></wxp>
<blockquote>
If this option is selected then metadata for Google Earth are generated for the tile tree. It means you can display the tiles as overlay of the virtual 3D world of the Google Earth desktop application or browser plug-in.
</blockquote>
</font>"""

step7 = """<h3>Step 7: Viewer Details</h3>
Please add informations related to the selected viewers.
<p>
<font color="#DC5309" size="large"><b>Info about the map</b></font>
<p>
Title of the map:<br/>
<wxp module="wx" class="TextCtrl" name="test" width="100%"><param name="name" value="title"></wxp>
<p>
Copyright notice:<br/>
<wxp module="wx" class="TextCtrl" name="test" width="100%"><param name="name" value="copyright"></wxp>
<p>
<font color="#DC5309" size="large"><b>The API keys for online maps API viewers</b></font>
<p>
Google Maps API key:<br/>
<wxp module="wx" class="TextCtrl" name="test" width="100%"><param name="name" value="googlekey"></wxp>
<font size="-1">
Note: You can get it <a href="http://code.google.com/apis/maps/signup.html">online at this adress</a>.
</font>
<p>
Yahoo Application ID key:<br/>
<wxp module="wx" class="TextCtrl" name="test" width="100%"><param name="name" value="yahookey"></wxp>
<font size="-1">
Note: You can get it <a href="http://developer.yahoo.com/wsregapp/">online at this adress</a>.
</font>"""
	
step8 = """<h3>Step 8: Rendering</h3>
Now you can start the rendering of the map tiles. It can be a time consuming process especially for large datasets... so be patient please.
<p>
<font color="#DC5309" size="large"><b>Rendering progress:</b></font>
<p>
<wxp module="wx" class="Gauge" name="g1" width="100%">
    <param name="name" value="progressbar">
</wxp>
<p>
<wxp module="wx" class="StaticText" name="progresstext" width="75%">
    <param name="name" value="progresstext">
    <param name="label" value="Click on the 'Render' button to start the rendering...">
</wxp>
<!--
With nice animation:
<wxp module="maptiler.widgets" class="ProgressPanel" name="progress" width="100%" height="50"><param name="name" value="progress"></wxp> -->
<p>&nbsp;
<p>
<font size="-1">
Thank you for using this software.<br/>
You can join <a href="http://groups.google.com/group/maptiler">MapTiler User Group</a> to speak with other MapTiler users and tell us about the maps you published!<br>
You can also check <a href="http://maptiler.uservoice.com/">MapTiler TODO list</a>, where you can vote for planned features or submit your own ideas for improvement, or you can <a href="http://code.google.com/p/maptiler/issues/list">report bugs</a>.
<p>
This is an open-source project. We welcome contribution from other programmers or <a href="http://www.maptiler.org/support/">donations or sponsorship</a> from our users. <b>Help us with improvement of this software!</b> <a href="http://help.maptiler.org/credits/">Sponsors and contributers</a>, thank you!
<p>
There is also an offer of <a href="http://www.maptiler.com/">commercial services and paid user-support</a> related to batch map tile rendering for big datasets, conversion of input geodata and development of new features.
</font>"""

stepfinal = """<h3>Your rendering task is finished!</h3>
Thank you for using this software. Now you can see the results. If you upload the directory with tiles to the Internet you map is published!
<p>
<font color="#DC5309" size="large"><b>Available results:</b></font>
<p>
The generated tiles and also the viewers are available in the output directory:
<p>
<b><a href="file://%s">%s</a></b>
<!--
<ul>
<li>Open the <a href="">Google Maps presentation</a> 
<li>Open the <a href="">OpenLayers presentation</a>
</ul>
-->
<p>&nbsp;
<p>&nbsp;
<p>
<center>
Please support development and maintainance of this software, without support we can not work on new versions... Even is you submit a small amount like one Euro or a Dollar it helps us!
<p>
VISA, MasterCard, American Express and other forms of payment as well as PayPal are available.
<p>
<a href="http://www.maptiler.org/support/">Support MapTiler</a>
</center>
"""

steps = [step1, step2, step3, step4, step5, step6, step7, step8 ]
