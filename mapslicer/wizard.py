#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import wx
import wx.html
import wx.lib.wxpTag
import webbrowser
import config
import icons

from wxgdal2tiles import wxGDAL2Tiles

# TODO: GetText
_ = lambda s: s

class WizardHtmlWindow(wx.html.HtmlWindow):
	def __init__(self, parent, id, pos=wx.DefaultPosition, size = wx.DefaultSize ):
		wx.html.HtmlWindow.__init__(self, parent, id, pos=pos, size=size, style=(wx.html.HW_NO_SELECTION |  wx.FULL_REPAINT_ON_RESIZE) )
		if "gtk2" in wx.PlatformInfo:
			self.SetStandardFonts()
		self.parent = parent
		self.step = 0

		# add the donate image to the MemoryFileSystem:
        mfs = wx.MemoryFSHandler()
        wx.FileSystem_AddHandler(mfs)

	def OnLinkClicked(self, linkinfo):
		webbrowser.open_new(linkinfo.GetHref())

	def GetActiveStep(self):
		return self.step 

	def SetStep(self, step):
		self.step = step
		if step >= len(steps):
			config.rendering = False
			config.resume = False
			self.SetPage(stepfinal % (config.outputdir, config.outputdir) )
			return
		self.SetPage(steps[step])
		if step == 1:
			self.FindWindowByName(config.profile).SetValue(1)
		elif step == 2:
			pass
			#self.FindWindowByName('nodatapanel').SetColor(config.nodata)
		elif step == 3:
			if not config.srs:
				config.customsrs = config.files[0][6]
				config.srs = config.customsrs
			if not config.srs and config.bboxgeoref:
				config.srsformat = 1
				config.srs = config.epsg4326
			self.FindWindowByName('srs').SetSelection(config.srsformat)
			self.FindWindowByName('srs').SetValue(config.srs)
		elif step == 4:
			g2t = wxGDAL2Tiles(['--profile',config.profile,'--s_srs', config.srs, str(config.files[0][2]) ])
			g2t.open_input()
			config.tminz = g2t.tminz
			config.tmaxz = g2t.tmaxz
			config.kml = g2t.kml
			del g2t

			self.FindWindowByName('tminz').SetValue(config.tminz)
			self.FindWindowByName('tmaxz').SetValue(config.tmaxz)

			if config.profile == 'gearth':
				self.FindWindowByName('format').SetItems( [
					_("PNG - with transparency"),
					_("JPEG - smaller but without transparency"),
					_("Hybrid JPEG+PNG - only for Google Earth"),
					_("Garmin Custom maps KMZ - 256 pixels"),
					_("Garmin Custom maps KMZ - 512 pixels"),
					_("Garmin Custom maps KMZ - 1024 pixels") ] )
			else:
				self.FindWindowByName('format').SetItems( [
					_("PNG - with transparency"),
					_("JPEG - smaller but without transparency"),
					_("Hybrid JPEG+PNG - only for Google Earth") ] )

			if not config.format and config.profile == 'gearth':
				self.FindWindowByName('format').SetSelection(2) # hybrid
			elif not config.format:
				self.FindWindowByName('format').SetSelection(0) # png
			else:
				self.FindWindowByName('format').SetSelection({'png':0,'jpeg':1,'hybrid':2,'garmin256':3,'garmin512':4,'garmin1024':5}[config.format])

			self.Refresh()
			self.Update()
		elif step == 5:
			filename = config.files[0][0]

			# If this is the first time the user has gone this far,
			# we try to come up with sensible default output directory.
			if config.outputdir is None:
				input_dir = os.path.dirname(filename)

				# Implicitly we try to place it in the same directory in
				# which the input file is located. But if this is not possible,
				# we try to use the current directory.
				if os.access(input_dir, os.W_OK):
					base_dir = input_dir
				else:
					base_dir = os.getcwd()

				# Default name is the same as the input file without extensions.
				config.outputdir = os.path.join(base_dir, os.path.splitext(os.path.basename( filename ))[0] )

			browseButton = self.FindWindowByName('browsebutton')
			if browseButton:
				browseButton.Bind(wx.EVT_BUTTON, self.OnBrowseButtonPressed)
			self.FindWindowByName('outputdir').SetValue(config.outputdir)

		elif step == 6:
			not_hybrid = config.format != 'hybrid'
			if config.profile=='mercator':
				self.FindWindowByName('google').Enable(not_hybrid)
				self.FindWindowByName('openlayers').Enable(not_hybrid)
				self.FindWindowByName('kml').Enable(True)
			elif config.profile=='geodetic':
				self.FindWindowByName('google').Enable(False)
				self.FindWindowByName('openlayers').Enable(not_hybrid)
				self.FindWindowByName('kml').Enable(True)
			elif config.profile=='raster':
				self.FindWindowByName('google').Enable(False)
				self.FindWindowByName('openlayers').Enable(not_hybrid)
				if not config.kml:
					self.FindWindowByName('kml').Enable(False)
			elif config.profile=='gearth':
				self.FindWindowByName('google').Enable(False)
				self.FindWindowByName('openlayers').Enable(not_hybrid)
				self.FindWindowByName('kml').Enable(True)

			self.FindWindowByName('google').SetValue(config.google)
			self.FindWindowByName('openlayers').SetValue(config.openlayers)
			self.FindWindowByName('kml').SetValue(config.kml)

		elif step == 7:
			config.title = os.path.basename( config.files[0][0] )
			self.FindWindowByName('title').SetValue(config.title)
			self.FindWindowByName('copyright').SetValue(config.copyright)
			self.FindWindowByName('googlekey').SetValue(config.googlekey)
			self.FindWindowByName('yahookey').SetValue(config.yahookey)

	def SaveStep(self, step):
		if step == 1:
			# Profile
			if self.FindWindowByName('mercator').GetValue():
				config.profile = 'mercator'
			elif self.FindWindowByName('geodetic').GetValue():
				config.profile = 'geodetic'
			elif self.FindWindowByName('raster').GetValue():
				config.profile = 'raster'
			elif self.FindWindowByName('gearth').GetValue():
				config.profile = 'gearth'
			print config.profile
		elif step == 2:
			# Files + Nodata
			print config.files
			config.nodata = self.FindWindowByName('nodatapanel').GetColor()
			print config.nodata
		elif step == 3:
			config.srs = self.FindWindowByName('srs').GetValue().encode('ascii','ignore').strip()
			config.srsformat = self.FindWindowByName('srs').GetSelection()
			print config.srs
		elif step == 4:
			config.tminz = int(self.FindWindowByName('tminz').GetValue())
			config.tmaxz = int(self.FindWindowByName('tmaxz').GetValue())

			format = self.FindWindowByName('format').GetCurrentSelection()
			config.format = ('png','jpeg','hybrid','garmin256','garmin512','garmin1024')[format]

			if config.format != 'hybrid':
				config.google = config.profile == 'mercator'
				config.openlayers = True
			else:
				config.google = False
				config.openlayers = False
			config.kml = config.profile in ('gearth', 'geodetic')

			print config.tminz
			print config.tmaxz
			print config.format
		elif step == 5:
			config.outputdir = self.FindWindowByName('outputdir').GetValue()
			config.url = self.FindWindowByName('url').GetValue()
			if config.url == 'http://':
				config.url = ''
		elif step == 6:
			config.google = self.FindWindowByName('google').GetValue()
			config.openlayers = self.FindWindowByName('openlayers').GetValue()
			config.kml = self.FindWindowByName('kml').GetValue()
		elif step == 7:
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

	def OnBrowseButtonPressed(self, evt):
		# browse button has been pressed to select output directory
		outputbox = self.FindWindowByName('outputdir')
		currentdir = outputbox.GetValue()
		dlg = wx.DirDialog(self, _("Choose output directory"), currentdir)
		if dlg.ShowModal() == wx.ID_OK:
			outputbox.SetValue(dlg.GetPath())

	def UpdateRenderProgress(self, complete):
		if self.step != len(steps) - 1:
			print _("Nothing to update - progressbar not displayed")
		else:
			progressbar = self.FindWindowByName('progressbar')
			progressbar.SetValue(complete)

	def UpdateRenderText(self, text):
		if self.step != len(steps) - 1:
			print _("Nothing to update - progresstext not displayed")
		else:
			progresstext = self.FindWindowByName('progresstext')
			progresstext.SetLabel(text)
			self.Layout()
			self.Refresh()

	def StartThrobber(self):
		self.FindWindowByName('throbber').Start()
		self.FindWindowByName('throbber').ToggleOverlay(False) 

	def StopThrobber(self):
		self.FindWindowByName('throbber').Stop()
		self.FindWindowByName('throbber').ToggleOverlay(True) 

step1 = "<h3>"+_("Selection of the tile profile")+'''</h3>
	<p>
	<font color="#DC5309" size="large"><b>'''+_("What kind of tiles would you like to generate?")+'''</b></font>
	<p>
	<font size="-1">
	<wxp module="wx" class="RadioButton" name="test">
	    <param name="label" value="'''+_("Google Maps compatible (Spherical Mercator)")+'''">
	    <param name="name" value="mercator">
	</wxp>
	<blockquote>
	'''+_("Mercator tiles compatible with Google, Yahoo or Bing maps and OpenStreetMap. Suitable for mashups and overlay with these popular interactive maps.")+'''
	</blockquote>
	<wxp module="wx" class="RadioButton" name="test">
	    <param name="label" value="'''+_("Google Earth (KML SuperOverlay)")+'''">
	    <param name="name" value="gearth">
	</wxp>
	<blockquote>
	'''+_('Tiles and KML metadata for 3D visualization in Google Earth desktop application or in the web browser plugin.')+''' 
	</blockquote>
	<wxp module="wx" class="RadioButton" name="test">
	    <param name="label" value="'''+_("WGS84 Plate Carree (Geodetic)")+'''">
	    <param name="name" value="geodetic">
	</wxp>
	<blockquote>
	'''+_('Compatible with most existing WMS servers, with the OpenLayers base map, Google Earth and other applications using WGS84 coordinates (<a href="http://www.spatialreference.org/ref/epsg/4326/">EPSG:4326</a>).')+'''
	</blockquote>
	<wxp module="wx" class="RadioButton" name="test">
	    <param name="label" value="'''+_("Image Based Tiles (Raster)")+'''">
	    <param name="name" value="raster">
	</wxp>
	<blockquote>
	'''+_("Tiles based on the dimensions of the picture in pixels (width and height). Stand-alone presentation even for images without georeference.")+'''
	</blockquote>
	</font>'''

step2 = '''<h3>'''+_("Source data files")+'''</h3>
	'''+_("Please choose the raster files of the maps you would like to publish.")+'''
	<p>
	<font color="#DC5309" size="large"><b>'''+_("Input raster map files:")+'''</b></font>
	<p>
	<!--
	<wxp module="wx" class="ListCtrl" name="listctrl" height="250" width="100%">
	    <param name="name" value="listctrl">
	</wxp>
	-->
	<wxp module="mapslicer.widgets" class="FilePanel" name="test" height="230" width=100%>
	<param name="name" value="filepanel"></wxp>
	<p>
	<wxp module="mapslicer.widgets" class="NodataPanel" name="test" height="30" width=100%>
	<param name="name" value="nodatapanel"></wxp>'''

step3 = '''<h3>'''+_("Spatial reference system (SRS)")+'''</h3>
	'''+_('It is necessary to know which coordinate system (Spatial Reference System) is used for georeferencing of the input files.')+'''
	<p>
	<font color="#DC5309" size="large"><b>'''+_("What is the Spatial Reference System used in your files?")+'''</b></font>
	<p>
	<wxp module="mapslicer.widgets" class="SpatialReferencePanel" name="test" height="260" width=100%>
	<param name="name" value="srs">
	</wxp>'''

step4 = '''<h3>'''+_("Details about the tile pyramid")+'''</h3> <!-- Zoom levels, Tile Format (PNG/JPEG) & Addressing, PostProcessing -->
	'''+_("In this step you should specify the details related to rendered tile pyramid.")+'''
	<p>
	<font color="#DC5309" size="large"><b>'''+_("Zoom levels to generate:")+'''</b></font>
	<p>
	'''+_("Minimum zoom:")+''' <wxp module="wx" class="SpinCtrl" name="test"><param name="value" value="0"><param name="name" value="tminz"></wxp> &nbsp;
	'''+_("Maximum zoom:")+''' <wxp module="wx" class="SpinCtrl" name="test"><param name="value" value="0"><param name="name" value="tmaxz"></wxp>
	<br>
	<font size="-1">
	'''+_("Note: The selected zoom levels are calculated from your input data and should be OK in most cases.")+'''
	</font>
	<p>
	<font color="#DC5309" size="large"><b>'''+_('Please choose a file format')+'''</b></font>
	<font size="-1">
	<p>
	<wxp module="wx" class="Choice" name="test">
		<param name="name" value="format">
		<param name="choices" value="(\''''+_("PNG - with transparency")+"','"+_("JPEG - smaller but without transparency")+"','"+_("Hybrid JPEG+PNG - only for Google Earth")+'''\')">
	</wxp>
	<p>
	<font size="-1">
	'''+_('Note: For PNG tiles, it may be advisable to use some kind of PNG compression tool on the produced tiles to optimise file sizes.')+'''
	</font>
	<!--
	<p>
	<font color="#DC5309" size="large"><b>Tile addressing:</b></font>
	<p>
	<font size="-1">
	<wxp module="wx" class="RadioButton" name="test"><param name="name" value="raster"><param name="label" value="OSGeo TMS - Tile Map Service"></wxp>
	<blockquote>
	Tile addressing used in open-source software tools. Info: <a href="http://wiki.osgeo.org/wiki/Tile_Map_Service_Specification">Tile Map Service</a>.
	</blockquote>
	<wxp module="wx" class="RadioButton" name="test"><param name="name" value="raster"><param name="label" value="Google - Native Google Adressing"></wxp>
	<blockquote>
	Native tile addressing used by Google Maps API. Info: <a href="http://code.google.com/apis/maps/documentation/overlays.html#Google_Maps_Coordinates">Google Maps Coordinates</a>
	</blockquote>
	<wxp module="wx" class="RadioButton" name="test"><param name="name" value="raster"><param name="label" value="Microsoft - QuadTree"></wxp>
	<blockquote>
	Tile addressing used in Microsoft products. Info: <a href="http://msdn.microsoft.com/en-us/library/bb259689.aspx">Virtal Earth Tile System</a>
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
	'''

step5 = '''<h3>'''+_("Destination folder and address")+'''</h3>
'''+_("Please select a directory where the generated tiles should be saved. Similarly you can specify the Internet address where will you publish the map.")+'''
<p>
<font color="#DC5309" size="large"><b>'''+_("Where to save the generated tiles?")+'''</b></font>
<p>
'''+_("Result directory:")+'''<br/>
<wxp module="wx" class="TextCtrl" name="outputdir" width="50%" height="30"><param name="name" value="outputdir"></wxp>
<wxp module="wx" class="Button"><param name="name" value="browsebutton"><param name="label" value="'''+_("Browse...")+'''"></wxp>
<p>
<font color="#DC5309" size="large"><b>'''+_("The Internet address (URL) for publishing the map:")+'''</b></font>
<p>
'''+_("Destination URL:")+'''<br/>
<wxp module="wx" class="TextCtrl" name="test" width="100%"><param name="name" value="url"><param name="value" value="http://"></wxp>
<p>
<font size="-1">
'''+_("Note: You should specify the URL if you need to generate the correct KML for Google Earth.")+'''
</font>'''

step6 = '''<h3>'''+_("Selection of the viewers")+'''</h3>
'''+_("MapSlicer can also generate simple web viewers for presenting the tiles as a map overlay. You can use these viewers as a base for your mashups. Similarly it is possible to generate KML files for Google Earth.")+'''
<p>
<font color="#DC5309" size="large"><b>'''+_("What viewers should be generated?")+'''</b></font>
<p>
<font size="-1">
<wxp module="wx" class="CheckBox" name="test"><param name="name" value="google"><param name="label" value="'''+_("Google Maps")+'''"></wxp>
<blockquote>
'''+_("Overlay presentation of your maps on top of standard Google Maps layers. If KML is generated then the Google Earth Plugin is used as well.")+'''
</blockquote>
<wxp module="wx" class="CheckBox" name="test"><param name="name" value="openlayers"><param name="label" value="'''+_("OpenLayers")+'''"></wxp>
<blockquote>
'''+_('Overlay of Google Maps, Bing Maps, Yahoo Maps, OpenStreetMap and OpenAerialMap, WMS and WFS layers and another sources available in the open-source project <a href="http://www.openlayers.org/">OpenLayers</a>.')+'''
</blockquote>
<wxp module="wx" class="CheckBox" name="test"><param name="name" value="kml"><param name="label" value="'''+("Google Earth (KML SuperOverlay)")+'''"></wxp>
<blockquote>
'''+_("If this option is selected then metadata for Google Earth is generated for the tile tree. It means you can display the tiles as an overlay of the virtual 3D world of the Google Earth desktop application or browser plug-in.")+'''
</blockquote>
</font>'''

step7 = '''<h3>'''+_("Details for generating the viewers")+'''</h3>
'''+_("Please add information related to the selected viewers.")+'''
<p>
<font color="#DC5309" size="large"><b>'''+_("Info about the map")+'''</b></font>
<p>
'''+_("Title of the map:")+'''<br/>
<wxp module="wx" class="TextCtrl" name="test" width="100%"><param name="name" value="title"></wxp>
<p>
'''+_("Copyright notice (optional):")+'''<br/>
<wxp module="wx" class="TextCtrl" name="test" width="100%"><param name="name" value="copyright"></wxp>
<p>
<font color="#DC5309" size="large"><b>'''+_("The API keys for online maps API viewers")+'''</b></font>
<p>
'''+_("Google Maps API key (optional):")+'''<br/>
<wxp module="wx" class="TextCtrl" name="test" width="100%"><param name="name" value="googlekey"></wxp>
<font size="-1">
'''+_('Note: You can get it <a href="http://code.google.com/apis/maps/signup.html">online at this address</a>.')+'''
</font>
<p>
'''+_("Yahoo Application ID key (optional):")+'''<br/>
<wxp module="wx" class="TextCtrl" name="test" width="100%"><param name="name" value="yahookey"></wxp>
<font size="-1">
'''+_('Note: You can get it <a href="http://developer.yahoo.com/wsregapp/">at this webpage</a>.')+'''
</font>'''

step8 = '''<h3>'''+_("Tile rendering")+'''</h3>
'''+_("Now you can start the rendering of the map tiles. It can be a time consuming process especially for large datasets... so be patient please.")+'''
<p>
<font color="#DC5309" size="large"><b>'''+_("Rendering progress:")+'''</b></font>
<p>
<wxp module="wx" class="Gauge" name="g1" width="100%">
    <param name="name" value="progressbar">
</wxp>
<center>
<wxp module="wx" class="StaticText" name="progresstext" width="450">
    <param name="style" value="wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE">
    <param name="name" value="progresstext">
    <param name="label" value="'''+_("Click on the 'Render' button to start the rendering...")+'''">
</wxp>
<p>
<wxp module="mapslicer.widgets" class="Throbber" name="throbber" width="16" height="16">
    <param name="name" value="throbber">
</wxp>
</center>
<font size="-1">
<p>&nbsp;
<br>'''+_("Thank you for using MapSlicer application.")+"<br>"+_('This is an open-source project - you can help us to make it better.')

# step9 - step8 with Resume button

# step10:
stepfinal = '''<h3>'''+_("Your rendering task is finished!")+'''</h3>
'''+_("Thank you for using this software. Now you can see the results. If you upload the directory with tiles to the Internet your map is published!")+'''
<p>
<font color="#DC5309" size="large"><b>'''+_("Available results:")+'''</b></font>
<p>
'''+_("The generated tiles and also the viewers are available in the output directory:")+'''
<p>
<center>
<b><a href="file://%s">%s</a></b><br>'''+_("(click to open)")+'''
</center>
<!--
<ul>
<li>Open the <a href="">Google Maps presentation</a> 
<li>Open the <a href="">OpenLayers presentation</a>
</ul>
-->
<p>&nbsp;
'''

steps = ['NULL',step1, step2, step3, step4, step5, step6, step7, step8 ]

