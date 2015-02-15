"""Basic file selector page; published ItemSelected events."""
# http://wxpython.org/docs/api/wx.ListCtrl-class.html

import os

import wx
import wx.combo
import wx.lib.hyperlink
import wx.lib.intctrl
import wx.lib.buttons
import wx.lib.throbber
import config
import webbrowser
import icons

import gdalpreprocess

# TODO: GetText
_ = lambda s: s

class FileDrop(wx.FileDropTarget):

	def __init__(self, target):
		wx.FileDropTarget.__init__(self)
		self.target = target

	def OnDropFiles(self, x, y, filenames):

		for name in filenames:
			try:
				file = open(name, 'r')
				file.close()
				self.target._add(name)
			except IOError, error:
				dlg = wx.MessageDialog(None, _('Error opening file\n') + str(error))
				dlg.ShowModal()
			except UnicodeDecodeError, error:
				dlg = wx.MessageDialog(None, _('Cannot open non ascii files\n') + str(error))
				dlg.ShowModal()


class FileListCtrl(wx.ListCtrl):
	def __init__(self, parent, id=-1, size=wx.DefaultSize):
		wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES|wx.LC_SINGLE_SEL|wx.SUNKEN_BORDER)

		self.InsertColumn(0, _("Filename"), width=350 )
		self.InsertColumn(1, _("Georeference"), width=115)

		self.SetItemCount(len(config.files))

		self.Bind(wx.EVT_SIZE, self.OnResize, self)

	def OnGetItemText(self, item, col):
		return config.files[item][col]

	def OnResize(self, event):
		"""Resize the filename column as the window is resized."""
		self.SetColumnWidth(0, self.GetClientSizeTuple()[0] - self.GetColumnWidth(1))
		event.Skip()


class FilePanel(wx.Panel):
	def __init__(self, parent, id=-1, size=wx.DefaultSize, name = ''):
		wx.Panel.__init__(self, parent, id, size=size, name=name)
		self.SetBackgroundColour('#ffffff')

		self.__items = []

		mainsizer = wx.BoxSizer(wx.VERTICAL)

		self.lc = FileListCtrl(self)
		dt = FileDrop(self)
		self.lc.SetDropTarget(dt)

		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.lc)
		self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected, self.lc)

		mainsizer.Add(self.lc, 1, wx.ALL|wx.EXPAND, 2)

		sizer = wx.FlexGridSizer(cols=5, hgap=5)
		badd = wx.Button(self, wx.ID_ADD)
		sizer.Add(badd)

		self.bdel = wx.Button(self, wx.ID_DELETE)
		sizer.Add(self.bdel)
		self.bdel.Disable()

		bup = wx.Button(self, wx.ID_UP)
		sizer.Add(bup)
		bup.Disable()
		bdown = wx.Button(self, wx.ID_DOWN)
		sizer.Add(bdown)
		bdown.Disable()

		bgeo = wx.Button(self, -1, _("Georeference"))
		sizer.Add(bgeo)
		mainsizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 3)

		self.SetSizer(mainsizer)
		self.Bind(wx.EVT_BUTTON, self.onAdd, badd)
		self.Bind(wx.EVT_BUTTON, self.onDelete, self.bdel)
		self.Bind(wx.EVT_BUTTON, self.onGeoreference, bgeo)

	def OnItemSelected(self, event):
		self.bdel.Enable()

	def OnItemDeselected(self, event):
		self.bdel.Disable()

	def _add(self, filename):

		if len(config.files) > 0:
			wx.MessageBox(_("""Unfortunately the merging of files is not yet implemented in the MapSlicer GUI. Only the first file in the list is going to be rendered."""), _("Not yet implemented"), wx.ICON_ERROR)

		filename = filename.encode('utf8')

		try:
			filerecord = gdalpreprocess.singlefile(filename)
			if filename:
				config.files = []
				config.files.append(filerecord)

				self.lc.SetItemCount(len(config.files))
				self.lc.Refresh(False)
				if len(config.files):
					self.bdel.Enable()
				self.resume = False
		except gdalpreprocess.PreprocessError, e:
			wx.MessageBox(str(e), _("Can't add a file"), wx.ICON_ERROR)

	def onAdd(self, evt):
		dlg = wx.FileDialog(
			self, message=_("Choose a file"),
			defaultDir=config.documentsdir,
			defaultFile="",
			wildcard=config.supportedfiles,
			style=wx.FD_OPEN
		)

		# Show the dialog and retrieve the user response. If it is the OK response,
		# process the data.
		if dlg.ShowModal() == wx.ID_OK:

			path = dlg.GetPath()
			print path, os.path.exists(path)

			if not os.path.exists(path):
				wx.MessageBox(_("MapSlicer can't find the following file:\n\n") + path,
					_("File not found"), wx.ICON_ERROR)
				return
			if not os.access(path, os.R_OK):
				wx.MessageBox(_("MapSlicer doesn't have permission to read the following file:\n\n") + path,
					_("Bad permissions"), wx.ICON_ERROR)
				return

			try:
				self._add(path)
			except gdalpreprocess.PreprocessError, e:
				wx.MessageBox(str(e), _("Can't add a file"), wx.ICON_ERROR)
				return

	def onDelete(self, evt):
		del config.files[ self.lc.GetFirstSelected() ]
		self.lc.SetItemCount(len(config.files))
		self.lc.Refresh()
		if not len(config.files):
			self.bdel.Disable()


	def onGeoreference(self, evt):
		bbox = None
		dlg = wx.TextEntryDialog(
				self, _("Please specify bounding box as 4 numbers or a world file as 6 numbers\nFormat: 'north south east west'\n\nAlternatively you can create a world file (.wld) or (.tab) by an external GIS software"),
				_('Georeference with bounding box'), '90 -90 180 -180')

		if dlg.ShowModal() == wx.ID_OK:
			str = dlg.GetValue()
			if str.find('.') == -1:
				str = str.replace(',','.')
			if str.find(',') != -1:
				str = str.replace(',',' ')
			print str
			try:
				bbox = map(float, str.split())
			except:
				return

			# Delete the old temporary files
			if config.files[ self.lc.GetFirstSelected() ][2] != config.files[ self.lc.GetFirstSelected() ][0]:
				os.unlink(config.files[ self.lc.GetFirstSelected() ][2])

			filename = config.files[ self.lc.GetFirstSelected() ][0]
			from gdalpreprocess import singlefile
			filerecord = singlefile(filename, bbox)
			if filerecord:
				config.files[self.lc.GetFirstSelected() ] = filerecord
				self.lc.Refresh(False)
				config.bboxgeoref = True

		dlg.Destroy()

	def onUp(self, evt):
		pass

	def onDown(self, evt):
		pass


class NodataPanel(wx.Panel):
	def __init__(self, parent, id=-1, size=wx.DefaultSize, name = '' ):
		wx.Panel.__init__(self, parent, id, size=size, name=name)
		self.SetBackgroundColour('#ffffff')

		sizer = wx.FlexGridSizer(cols=2, hgap=5)
		self.ch1 = wx.CheckBox(self, -1, _("Set transparency for a color (NODATA):"))
		sizer.Add(self.ch1)

		if config.nodata:
			self.color = config.nodata
			self.ch1.SetValue(True)
		else:
			self.ch1.SetValue(False)
			self.color = (0,0,0)

		bmp = wx.EmptyBitmap(16, 16)
		dc = wx.MemoryDC(bmp)
		dc.SetBackground(wx.Brush(self.color))
		dc.Clear()
		del dc

		self.bcolor = wx.BitmapButton(self, -1, bmp)
		sizer.Add(self.bcolor)

		self.SetSizer(sizer)
		self.Bind(wx.EVT_BUTTON, self.onColor, self.bcolor)


	def onColor(self, evt):
		color = wx.ColourData()
		color.SetColour(self.color)
		dlg = wx.ColourDialog(self, data=color)

		# Ensure the full colour dialog is displayed,
		# not the abbreviated version.
		dlg.GetColourData().SetChooseFull(True)

		if dlg.ShowModal() == wx.ID_OK:

			# If the user selected OK, then the dialog's wx.ColourData will
			# contain valid information. Fetch the data.
			data = dlg.GetColourData()

			# ... then do something with it. The actual colour data will be
			# returned as a three-tuple (r, g, b)
			self.color = data.GetColour().Get()
			#print 'You selected: %s\n' % str(self.color)

			bmp = wx.EmptyBitmap(16, 16)
			dc = wx.MemoryDC(bmp)
			dc.SetBackground(wx.Brush(data.GetColour().Get()))
			dc.Clear()

			self.bcolor.SetBitmapLabel(bmp)
			self.ch1.SetValue(True)
			config.nodata = self.color

		# Once the dialog is destroyed, Mr. wx.ColourData is no longer your
		# friend. Don't use it again!
		dlg.Destroy()

	def GetColor(self):
		if self.ch1.GetValue():
			return self.color
		else:
			return None

class SpatialReferencePanel(wx.Panel):
	def __init__(self, parent, id=-1, size=wx.DefaultSize, name = ''):
		wx.Panel.__init__(self, parent, id, size=size, name=name)
		#self.SetBackgroundColour(wx.Colour(255, 30, 50))
		self.SetBackgroundColour('#ffffff')

		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.ch1 = wx.Choice(self, -1, choices = config.srsFormatList)
		self.ch1.SetSelection(0)
		self.sizer.Add(self.ch1, 0, wx.EXPAND|wx.ALL, 3)

		# EPSG/ESRI codes
		epsgsizer = wx.BoxSizer(wx.HORIZONTAL)
		self.epsgesri = wx.Choice(self, -1, choices = ['EPSG','ESRI'])
		self.epsgesri.SetSelection(0)
		epsgsizer.Add(self.epsgesri, 0, wx.EXPAND|wx.RIGHT|wx.LEFT, 3)
		self.epsgcode = wx.lib.intctrl.IntCtrl(self, value=4326, allow_none=True)
		epsgsizer.Add(self.epsgcode, 0, wx.EXPAND|wx.RIGHT|wx.LEFT, 3)
		self.epsgbutton = wx.Button(self, -1, "Set")
		epsgsizer.Add(self.epsgbutton, 0, wx.EXPAND|wx.RIGHT|wx.LEFT, 3)
		link = wx.lib.hyperlink.HyperLinkCtrl(self, -1, _("EPSG Registry"), URL="http://www.epsg-registry.org/")
		link.SetBackgroundColour('#ffffff')
		epsgsizer.Add(link, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 3)
		self.sizer.Add(epsgsizer, 0, wx.EXPAND)

		# Search SpatialReference.org
		searchsizer = wx.BoxSizer(wx.VERTICAL)
		self.search = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
		searchsizer.Add(self.search, 1, wx.EXPAND|wx.BOTTOM, 4)
		text = wx.StaticText(self, -1, _('Paste here the "OGC WKT" or "Proj4" definition or the URL:'))
		searchsizer.Add(text, 0, wx.ALIGN_CENTER|wx.TOP, 3)
		# 'Paste here WKT definition or URL of the spatial reference system, like:\n'
		self.sizer.Add(searchsizer, 0, wx.EXPAND|wx.ALL, 3)

		# UTM - Universal Transverse Mercator
		utmsizer = wx.BoxSizer(wx.HORIZONTAL)
		text = wx.StaticText(self, -1, _('UTM Zone:'))
		utmsizer.Add(text, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
		self.utmzone = wx.lib.intctrl.IntCtrl(self, value=30, allow_none=True)
		utmsizer.Add(self.utmzone, 1, wx.EXPAND|wx.RIGHT|wx.LEFT, 3)
		self.north = wx.Choice(self, -1, choices = ['north','south'])
		self.north.SetSelection(0)
		utmsizer.Add(self.north, 0, wx.EXPAND|wx.RIGHT|wx.LEFT, 3)
		self.geogcs = wx.Choice(self, -1, choices = config.wellknowngeogcs)
		self.geogcs.SetSelection(0)
		utmsizer.Add(self.geogcs, 0, wx.EXPAND|wx.RIGHT, 3)
		self.utmbutton = wx.Button(self, -1, _("Set"))
		utmsizer.Add(self.utmbutton, 0, wx.EXPAND|wx.RIGHT|wx.LEFT, 3)
		self.sizer.Add(utmsizer, 0, wx.EXPAND|wx.ALL, 3)

		self.tc1 = wx.TextCtrl(self, -1, config.srs, style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
		self.sizer.Add(self.tc1, 1, wx.EXPAND|wx.ALL, 3)
		self.bpreview = wx.Button(self, -1, _("Preview the map reference with this SRS"))
		self.sizer.Add(self.bpreview, 0, wx.ALL, 3)

		if config.srsformat != 3:
			self.sizer.Hide(1, recursive=True) # EPSG
		if config.srsformat != 4:
			self.sizer.Hide(2, recursive=True) # Search
		if config.srsformat != 2:
			self.sizer.Hide(3, recursive=True) # UTM
		self.sizer.Layout()

		self.SetSizer(self.sizer)

		self.Bind(wx.EVT_BUTTON, self.Set, self.utmbutton)
		self.Bind(wx.EVT_BUTTON, self.Set, self.epsgbutton)
		self.Bind(wx.EVT_BUTTON, self.Preview, self.bpreview)
		self.Bind(wx.EVT_CHOICE, self.Choice, self.ch1)
		self.Bind(wx.EVT_TEXT_ENTER, self.Search, self.search)
		self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.Search, self.search)

	def Search(self, evt):
		what = self.search.GetValue()
		what += " PROJCS"
		webbrowser.open_new("http://www.spatialreference.org/ref/?search=%s" % what)

	def Choice(self, evt):
		ch = self.ch1.GetSelection()
		if ch==0: # Custom
			self.SetValue(config.customsrs)
			self.sizer.Hide(1, recursive=True) # EPSG
			self.sizer.Hide(2, recursive=True) # Search
			self.sizer.Hide(3, recursive=True) # UTM
			self.sizer.Layout()
		elif ch==1: # WGS84
			self.SetValue(config.epsg4326)
			self.sizer.Hide(1, recursive=True) # EPSG
			self.sizer.Hide(2, recursive=True) # Search
			self.sizer.Hide(3, recursive=True) # UTM
			self.sizer.Layout()
		elif ch==2: # UTM
			self.SetValue('')
			self.sizer.Hide(1, recursive=True) # EPSG
			self.sizer.Hide(2, recursive=True) # Search
			self.sizer.Show(3, recursive=True) # UTM
			self.sizer.Layout()
		elif ch==3: # EPSG
			self.SetValue('')
			self.sizer.Show(1, recursive=True) # EPSG
			self.sizer.Hide(2, recursive=True) # Search
			self.sizer.Hide(3, recursive=True) # UTM
			self.sizer.Layout()
		elif ch==4: # Search
			self.SetValue('')
			self.sizer.Hide(1, recursive=True) # EPSG
			self.sizer.Show(2, recursive=True) # Search
			self.sizer.Hide(3, recursive=True) # UTM
			self.sizer.Layout()

	def Set(self, evt):
		try:
			from osgeo import osr
			osr.UseExceptions()
			source = osr.SpatialReference()
			# 0 = Custom
			if self.GetSelection() == 1: # WGS84
				self.SetValue(config.epsg4326)
			elif self.GetSelection() == 2: # UTM
				source.SetProjCS( _("%s / UTM Zone %s%s") % (config.wellknowngeogcs[self.geogcs.GetSelection()], self.utmzone.GetValue(), ['N','S'][self.north.GetSelection()] ));
				source.SetWellKnownGeogCS( config.wellknowngeogcs[self.geogcs.GetSelection()] );
				source.SetUTM( self.utmzone.GetValue(), (self.north.GetSelection()==0) );
				self.SetValue(source.ExportToPrettyWkt())
			elif self.GetSelection() == 3: # EPSG
				if self.epsgesri.GetSelection() == 0:
					source.ImportFromEPSG( self.epsgcode.GetValue() )
				else:
					source.ImportFromESRI( self.epsgcode.GetValue() )
				self.SetValue(source.ExportToPrettyWkt())
		except Exception, error:
			wx.MessageBox("%s" % error , _("The SRS definition is not correct"), wx.ICON_ERROR)


	def Preview(self, evt):
		try:
			from gdalpreprocess import SRSInput
			srs = SRSInput(self.GetValue())
			filerecord = config.files[0]
			T = filerecord[3]
			xsize, ysize = filerecord[4:6]
			from osgeo import osr
			source = osr.SpatialReference()
			source.SetFromUserInput( srs )
			wgs84 = osr.SpatialReference()
			wgs84.ImportFromEPSG( 4326 )
			trans = osr.CoordinateTransformation(source, wgs84)
			ulx, uly = trans.TransformPoint(T[0], T[3])[:2]
			urx, ury = trans.TransformPoint(T[0] + T[1]*xsize, T[3] + T[4]*xsize)[:2]
			llx, lly = trans.TransformPoint(T[0] + T[2]*ysize, T[3] + T[5]*ysize)[:2]
			lrx, lry = trans.TransformPoint(T[0] + T[1]*xsize + T[2]*ysize, T[3] + T[4]*xsize + T[5]*ysize )[:2]
			webbrowser.open_new("http://www.mapslicer.org/preview/?points=%.10f,%.10f,%.10f,%.10f,%.10f,%.10f,%.10f,%.10f" %
				(uly, ulx, ury, urx, lry, lrx, lly, llx))
		except Exception, error:
			wx.MessageBox("%s" % error , _("The SRS definition is not correct"), wx.ICON_ERROR)

	def SetValue(self, value):
		self.tc1.SetValue(value)

	def GetValue(self):
		return self.tc1.GetValue().encode('ascii','ignore')

	def SetSelection(self, value):
		return self.ch1.SetSelection(value)

	def GetSelection(self):
		return self.ch1.GetSelection()

class Throbber(wx.lib.throbber.Throbber):

	def __init__(self, parent, id=-1, icon="", pos=wx.DefaultPosition, size=wx.DefaultSize, name=""):
		wx.lib.throbber.Throbber.__init__(self, parent, id, icons.getThrobberBitmap(), pos, size, frames=12, frameWidth=16, overlay=icons.getWhite16Bitmap(), name=name)

