#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TODO: Cleaning the code, refactoring before 1.0 publishing

import os, sys
import wx
import wx.lib.delayedresult as delayedresult # threading in wx

import config
import icons
import wizard
import widgets

# TODO: GetText
from config import _

import gdalpreprocess
from wxgdal2tiles import wxGDAL2Tiles

class MainFrame(wx.Frame):
	def __init__(self, *args, **kwds):
		
		self.abortEvent = delayedresult.AbortEvent()
		self.jobID = 0
		self.rendering = False
		self.resume = False
		
		# begin wxGlade: MainFrame.__init__
		kwds["style"] = wx.DEFAULT_FRAME_STYLE
		wx.Frame.__init__(self, *args, **kwds)
		
		self.panel_1 = wx.Panel(self, -1)
		self.panel_2 = wx.Panel(self.panel_1, -1)
		
		# Menu Bar
		self.main_frame_menubar = wx.MenuBar()

		menu = wx.Menu()
		item = menu.Append(wx.NewId(), _("Insert &raster map files"))
		self.Bind(wx.EVT_MENU, self.OnOpen, item)
		#item = menu.Append(wx.ID_PREFERENCES, _("&Preferences"))
		#self.Bind(wx.EVT_MENU, self.OnPrefs, item)
		item = menu.Append(wx.ID_EXIT, _("&Exit"))
		self.Bind(wx.EVT_MENU, self.OnQuit, item)
		self.main_frame_menubar.Append(menu, _("&File"))
		
		menu = wx.Menu()
		item = menu.Append(wx.ID_HELP, _("Online &Help && FAQ"))
		self.Bind(wx.EVT_MENU, self.OnHelp, item)
		item = menu.Append(wx.NewId(), _("MapTiler user &group"))
		self.Bind(wx.EVT_MENU, self.OnGroupWeb, item)
		item = menu.Append(wx.NewId(), _("Project &website"))
		self.Bind(wx.EVT_MENU, self.OnProjectWeb, item)
		item = menu.Append(wx.ID_ABOUT, _("&About"))
		self.Bind(wx.EVT_MENU, self.OnAbout, item)
		self.main_frame_menubar.Append(menu, _("&Help"))

		self.SetMenuBar(self.main_frame_menubar)

		# Events
		self.Bind(wx.EVT_CLOSE, self.OnQuit)
		#self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio)
		
		# Menu Bar end
		self.bitmap_1 = wx.StaticBitmap(self, -1, icons.getIcon140Bitmap()) # wx.Bitmap("../resources/icon140.png", wx.BITMAP_TYPE_ANY))
		self.steplabel = []
		self.steplabel.append(wx.StaticText(self, -1, _("Tile Profile")))
		self.steplabel.append(wx.StaticText(self, -1, _("Source Data Files")))
		self.steplabel.append(wx.StaticText(self, -1, _("Spatial Reference")))
		self.steplabel.append(wx.StaticText(self, -1, _("Tile Details"))) # Zoom levels, PNG/JPEG, Tile adressing, Postprocessing? 
		self.steplabel.append(wx.StaticText(self, -1, _("Destination"))) # Directory / database
		self.steplabel.append(wx.StaticText(self, -1, _("Viewers")))
		self.steplabel.append(wx.StaticText(self, -1, _("Viewer Details")))
		self.steplabel.append(wx.StaticText(self, -1, _("Rendering")))
		
		self.label_10 = wx.StaticText(self, -1, _("MapTiler - Map Tile Generator for Mashups"))

		#converts geographic raster data (TIFF/GeoTIFF, MrSID, ECW, JPEG2000, Erdas HFA, NOAA BSB, JPEG, ...) into
		self.html = wizard.WizardHtmlWindow(self.panel_2, -1)
		self.html.SetBorders(2)
		self.html.SetStep(0)
		
		#self.html = widgets.FilePanel(self.panel_2, -1)

		self.label_8 = wx.StaticText(self, -1, _("http://www.maptiler.org/"))
		self.label_9 = wx.StaticText(self, -1, _(u"(C) 2008 - Klokan Petr Přidal"))

		self.button_back = wx.Button(self, -1, _("Go &Back"))
		self.Bind(wx.EVT_BUTTON, self.OnBack, self.button_back)
		self.button_continue = wx.Button(self, -1, _("&Continue"))
		self.Bind(wx.EVT_BUTTON, self.OnContinue, self.button_continue)

		self.__set_properties()
		self.__do_layout()
		# end wxGlade

	def __set_properties(self):
		# begin wxGlade: MainFrame.__set_properties
		self.SetTitle(_("MapTiler - Map Tile Generator for Mashups"))
		#self.SetIcon( icons.getIconIcon() )
		self.SetBackgroundColour(wx.Colour(253, 253, 253))
		for label in self.steplabel[1:]:
			label.Enable(False)
		self.label_10.SetForegroundColour(wx.Colour(220, 83, 9))
		self.label_10.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
		self.html.SetMinSize((500, 385))
		self.panel_2.SetBackgroundColour(wx.Colour(255, 255, 255))
		self.panel_1.SetBackgroundColour(wx.Colour(192, 192, 192))
		self.label_8.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
		self.label_9.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
		self.button_back.Enable(False)
		self.button_continue.SetDefault()
		# end wxGlade

	def __do_layout(self):
		# begin wxGlade: MainFrame.__do_layout
		sizer_1 = wx.BoxSizer(wx.VERTICAL)
		sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_5 = wx.BoxSizer(wx.VERTICAL)
		sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_6 = wx.BoxSizer(wx.VERTICAL)
		sizer_9 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_10 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_4 = wx.BoxSizer(wx.VERTICAL)
		sizer_8 = wx.BoxSizer(wx.VERTICAL)
		sizer_4.Add(self.bitmap_1, 0, wx.BOTTOM, 25)
		for label in self.steplabel:
			sizer_8.Add(label, 0, wx.ALL, 5)
		sizer_4.Add(sizer_8, 1, wx.LEFT|wx.EXPAND, 15)
		sizer_2.Add(sizer_4, 0, wx.RIGHT|wx.EXPAND, 5)
		sizer_6.Add(self.label_10, 0, wx.TOP|wx.BOTTOM, 15)
		sizer_10.Add(self.html, 1, wx.ALL|wx.EXPAND, 30)
		self.panel_2.SetSizer(sizer_10)
		sizer_9.Add(self.panel_2, 1, wx.ALL|wx.EXPAND, 2)
		self.panel_1.SetSizer(sizer_9)
		sizer_6.Add(self.panel_1, 1, wx.ALL|wx.EXPAND, 2)
		sizer_2.Add(sizer_6, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
		sizer_1.Add(sizer_2, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 15)
		sizer_5.Add(self.label_8, 0, 0, 0)
		sizer_5.Add(self.label_9, 0, 0, 0)
		sizer_3.Add(sizer_5, 1, wx.EXPAND, 0)
		sizer_3.Add(self.button_back, 0, wx.RIGHT, 10)
		sizer_3.Add(self.button_continue, 0, wx.RIGHT, 10)
		sizer_1.Add(sizer_3, 0, wx.ALL|wx.EXPAND, 15)
		self.SetSizer(sizer_1)
		sizer_1.SetSizeHints(self)
		#sizer_1.Fit(self)
		self.Layout()
		self.Centre(wx.BOTH)
		#self.SetMinSize((700, 500))
		# end wxGlade

	def OnQuit(self,Event):
		self.Destroy()

	def OnAbout(self, event):
		# First we create and fill the info object
		info = wx.AboutDialogInfo()
		info.Name = "MapTiler"
		info.Version = config.version
		info.Copyright = "(C) 2008 Klokan Petr Pridal"
		info.Description =	"""MapTiler is a powerful tool for online map publishing and generation of raster overlay mashups.
Your geodata are transformed to the tiles compatible with Google Maps and Earth - ready for uploading to your webserver."""

		#info.WebSite = ("http://www.maptiler.org/", "MapTiler HomePage")
		#info.Developers = [ "Joe Programmer", "Jane Coder", "Vippy the Mascot" ]
		#info.License = """New BSD License"""

		# Then we call wx.AboutBox giving it that info object
		wx.AboutBox(info)

	def OnProjectWeb(self, event):
		webbrowser.open_new(_("http://www.maptiler.org"))

	def OnGroupWeb(self, event):
		webbrowser.open_new(_("http://groups.google.com/group/maptiler"))

	def OnHelp(self, event):
		webbrowser.open_new(_("http://help.maptiler.org"))

	def OnOpen(self, event):
		dlg = wx.FileDialog(
			self, message="Choose a file",
			defaultDir=os.getcwd(),
			defaultFile="",
			wildcard=config.supportedfiles,
			style=wx.OPEN | wx.MULTIPLE #| wx.CHANGE_DIR
			)

		# Show the dialog and retrieve the user response. If it is the OK response, 
		# process the data.
		if dlg.ShowModal() == wx.ID_OK:
			paths = dlg.GetPaths()

			for path in paths:
				self._add(path)
				
		dlg.Destroy()
		step = self.html.GetActiveStep()
		self.html.SaveStep(step)
		self.html.SetStep(1)

	def OnPrefs(self, event):
		dlg = wx.MessageDialog(self, "This would be an preferences Dialog\n"
									 "If there were any preferences to set.\n",
								"Preferences", wx.OK | wx.ICON_INFORMATION)
		dlg.ShowModal()
		dlg.Destroy()
		
	def OnBack(self, event):
		step = self.html.GetActiveStep()
		if step > 0 and not self.rendering:
			self.steplabel[step].Enable(False)
			self.html.SaveStep(step)
			self.html.SetStep( step - 1 )
		if step == 7 and not self.rendering:
			self.button_continue.SetLabel(_("&Continue"))
		if step == 7 and self.rendering:
			self.button_continue.Enable()
			self.button_continue.SetLabel(_("&Resume"))
			self.button_back.SetLabel(_("Go &Back"))
			self._renderstop()
		if step == 0:
			self.button_back.Enable(False)
		
	def OnContinue(self, event):
		self.button_back.Enable()
		step = self.html.GetActiveStep()
		self.html.SaveStep(step)
		if step == 1:
			if len(config.files) == 0:
				wx.MessageBox("""You have to add some files for rendering""", "No files specified", wx.ICON_ERROR)
				return
			if config.files[0][1] == '' and config.profile != 'raster':
				wx.MessageBox("""Sorry the file you have specified does not have georeference.\n\nClick on the 'Georeference' button and give a bounding box or \ncreate a world file (.wld) for the specified file.""", "Missing georeference", wx.ICON_ERROR)
				return
		if step == 2:
			srs = gdalpreprocess.SRSInput(config.srsformat, config.srs)
			if config.profile != 'raster' and not srs:
				wx.MessageBox("""You have to specify refenrece system of your coordinates.\n\nTIP: for latitude/longitude in WGS84 you should type 'EPSG:4326'""", "Not valid spatial reference system", wx.ICON_ERROR)
				return
			else:
				config.srs = srs
		if step == 6:
			self.button_continue.SetLabel(_("&Render"))
		if step == 7:
			self.button_back.SetLabel(_("&Stop"))
			self.button_continue.Enable(False)
			self._renderstart()
		if step < 7: # maximum is 7
			self.html.SetStep( step + 1 )
			self.steplabel[step+1].Enable()
		if step > 7:
			self.Destroy()
			
	def _add(self, filename):

		filename = filename.encode('utf8')
		
		if len(config.files) > 0:
			wx.MessageBox("""Unfortunately the merging of files is not yet implemented in the MapTiler GUI. Only the first file in the list is going to be rendered.""", "MapTiler: Not yet implemented :-(", wx.ICON_ERROR)

		filerecord = gdalpreprocess.singlefile(filename)
		if filename:
			config.files.append(filerecord)
		
	def _renderstop(self):
		
		self.g2t.stop()
		self.abortEvent.set()
		self.rendering = False
		self.resume = True
		self.html.UpdateRenderText("Rendering stopped !!!!")
			
	def _renderstart(self):
		self.abortEvent.clear()
		self.rendering = True
		self.html.UpdateRenderText("Started...")
		self.jobID += 1
		
		params = self.createParams()
		print "-"*20
		for p in params:
			print type(p), p
		#params = ['--s_srs','EPSG:4326','/Users/klokan/Desktop/fox-denali-alaska-644060-xl.jpg']
		
		delayedresult.startWorker(self._resultConsumer, self._resultProducer,
				wargs=(self.jobID,self.abortEvent, params), jobID=self.jobID)
	
	def createParams(self):
		
		config.srs = "EPSG:4326"
		params = ['--profile',config.profile,
			'--s_srs',config.srs,
			'--zoom',"%i-%i" % (config.tminz, config.tmaxz)
			#'--title',config.title,
			#'--copyright',config.copyright,
			]
		viewer = 'none'
		if config.google:
			viewer = 'google'
		if config.openlayers:
			viewer = 'openlayers'
		if config.google and config.openlayers:
			viewer = 'all'
		params.extend(['--webviewer',viewer])
		if config.kml:
			params.append('--force-kml')
		
		if config.url:
			params.extend(['--url',config.url])
		if config.googlekey:
			params.extend(['--googlekey',config.googlekey])
		if config.yahookey:
			params.extend(['--yahookey',config.googlekey])

		# And finally the files
		params.append( config.files[0][2].encode('utf-8') )
	
		# and output directory
		params.append( config.outputdir )

		return params


	def _resultProducer(self, jobID, abortEvent, params):

		#params = ['first.tif']
		#params = ['--s_srs','EPSG:4326','/Users/klokan/Desktop/fox-denali-alaska-644060-xl.jpg']
		if self.resume and params[0] != '--resume':
			params.insert(0, '--resume')
		
		self.g2t = wxGDAL2Tiles( params )
		self.g2t.setProgressObject( self.html )

		self.html.UpdateRenderText("Opening the input files")
		self.g2t.open_input()
		# Opening and preprocessing of the input file

		if not self.g2t.stopped and not abortEvent():
			self.html.UpdateRenderText("Generating viewers and metadata")
			# Generation of main metadata files and HTML viewers
			self.g2t.generate_metadata()

		if not self.g2t.stopped and not abortEvent():
			self.html.UpdateRenderText("Rendering the base tiles")
			# Generation of the lowest tiles
			self.g2t.generate_base_tiles()

		if not self.g2t.stopped and not abortEvent():
			self.html.UpdateRenderText("Rendering the overview tiles in the pyramid")
			# Generation of the overview tiles (higher in the pyramid)
			self.g2t.generate_overview_tiles()

	
	def _resultConsumer(self, delayedResult):
		jobID = delayedResult.getJobID()
		assert jobID == self.jobID
		try:
			result = delayedResult.get()
		except Exception, exc:
			#print "Result for job %s raised exception: %s" % (jobID, exc)
			return

		if not self.g2t.stopped:
			self.html.UpdateRenderText("Task is finished!")
			self.html.SetStep(9)
			self.button_back.Hide()
			self.button_continue.SetLabel("Exit")
			self.button_continue.Enable()


# end of class MainFrame
