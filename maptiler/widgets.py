"""Basic file selector page; published ItemSelected events."""
# http://wxpython.org/docs/api/wx.ListCtrl-class.html
# TODO: Cleaning the code, refactoring before 1.0 publishing

import os

import wx
import wx.combo
import config

import gdalpreprocess

from config import _, nodata

class FileDrop(wx.FileDropTarget):

	def __init__(self, target):
		wx.FileDropTarget.__init__(self)
		self.target = target

	def OnDropFiles(self, x, y, filenames):

		for name in filenames:
			try:
				file = open(name, 'r')
				#print name
				#text = file.read()
				#self.window.WriteText(text)
				file.close()
				self.target._add(name)
			except IOError, error:
				dlg = wx.MessageDialog(None, 'Error opening file\n' + str(error))
				dlg.ShowModal()
			except UnicodeDecodeError, error:
				dlg = wx.MessageDialog(None, 'Cannot open non ascii files\n' + str(error))
				dlg.ShowModal()


class FileListCtrl(wx.ListCtrl):
	def __init__(self, parent, id=-1, size=wx.DefaultSize):
		wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES|wx.LC_SINGLE_SEL|wx.SUNKEN_BORDER)
		
		self.InsertColumn(0, _("Filename"), width=350 )
		self.InsertColumn(1, _("Georeference"), width=115)
		
		self.SetItemCount(len(config.files))
		#self..Refresh(False)
		
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
		#self.__items.append('Test')

		mainsizer = wx.BoxSizer(wx.VERTICAL)
		
		self.lc = FileListCtrl(self)
		#lc.SetWindowStyleFlag(wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES|wx.LC_SINGLE_SEL) #|wx.LC_AUTOARRANGE) #|wx.SUNKEN_BORDER)
		#lc.InsertColumn(0, _("Filename"), width=350 ) #wx.LIST_AUTOSIZE)
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

		bgeo = wx.Button(self, -1, "Georeference")
		sizer.Add(bgeo)
		mainsizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 3)
		
		self.SetSizer(mainsizer)
		self.Bind(wx.EVT_BUTTON, self.onAdd, badd)
		self.Bind(wx.EVT_BUTTON, self.onDelete, self.bdel)

	def OnItemSelected(self, event):
		self.bdel.Enable()
		#print 'OnItemSelected: "%s"' % event.m_itemIndex

	def OnItemDeselected(self, event):
		self.bdel.Disable()

	def _add(self, filename):

		if len(config.files) > 0:
			wx.MessageBox("""Unfortunately the merging of files is not yet implemented in the MapTiler GUI. Only the first file in the list is going to be rendered.""", "MapTiler: Not yet implemented :-(", wx.ICON_ERROR)
		
		filerecord = gdalpreprocess.singlefile(filename)
		if filename:
			config.files.append(filerecord)
		
			self.lc.SetItemCount(len(config.files))
			self.lc.Refresh(False)
			if len(config.files):
				self.bdel.Enable()
	
	def onAdd(self, evt):
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
			# This returns a Python list of files that were selected.
			paths = dlg.GetPaths()

			#print 'You selected %d files:' % len(paths)

			for path in paths:
				#print '%s\n' % path
				#files.append([filename,"None"])
				#self.lc.SetItemCount(len(files))
				self._add(path)
				
	def onDelete(self, evt):
		del config.files[ self.lc.GetFirstSelected() ]
		self.lc.SetItemCount(len(config.files))
		self.lc.Refresh()
		if not len(config.files):
			self.bdel.Disable()
		
	
	def onGeoreference(self, evt):
		pass
	
	def onUp(self, evt):
		pass
	
	def onDown(self, evt):
		pass
        

class NodataPanel(wx.Panel):
	def __init__(self, parent, id=-1, size=wx.DefaultSize, name = '' ):
		wx.Panel.__init__(self, parent, id, size=size, name=name)
		self.SetBackgroundColour('#ffffff')

		sizer = wx.FlexGridSizer(cols=2, hgap=5)
		self.ch1 = wx.CheckBox(self, -1, "Set transparency for a color (NODATA):")
		sizer.Add(self.ch1)
		
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
		
		self.ch1.Enable(False)
		self.bcolor.Enable(False)
		
	def onColor(self, evt):
		color = wx.ColourData()
		color.SetColour(self.color)
		dlg = wx.ColourDialog(self, data=color)

		# Ensure the full colour dialog is displayed, 
		# not the abbreviated version.
		dlg.GetColourData().SetChooseFull(True)

		if dlg.ShowModal() == wx.ID_OK:

			# If the user selected OK, then the dialog's wx.ColourData will
			# contain valid information. Fetch the data ...
			data = dlg.GetColourData()

			# ... then do something with it. The actual colour data will be
			# returned as a three-tuple (r, g, b) in this particular case.
			self.color = data.GetColour().Get()
			#print 'You selected: %s\n' % str(self.color)

			bmp = wx.EmptyBitmap(16, 16)
			dc = wx.MemoryDC(bmp)
			dc.SetBackground(wx.Brush(data.GetColour().Get()))
			dc.Clear()
						
			self.bcolor.SetBitmapLabel(bmp)
			self.ch1.SetValue(True)

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

		sizer = wx.BoxSizer(wx.VERTICAL)
		ch1 = wx.Choice(self, -1, choices = config.srsFormatList)
		ch1.SetSelection(0)
		sizer.Add(ch1, 0, wx.EXPAND|wx.ALL, 3)
		tc1 = wx.TextCtrl(self, -1, "EPSG:4326", style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
		sizer.Add(tc1, 1, wx.EXPAND|wx.ALL, 3)

		self.SetSizer(sizer)

class ProgressPanel(wx.Panel):

	def __init__(self, parent, id=-1, size=wx.DefaultSize, name=''):
		wx.Panel.__init__(self, parent, id, size=size, name=name)
		self.SetBackgroundColour('#ffffff')
		
		self.value = 0

		vsizer = wx.BoxSizer(wx.VERTICAL)
		
		self.g1 = wx.Gauge(self, -1)
		vsizer.Add(self.g1, 1, wx.EXPAND|wx.ALL,0)

		hsizer = wx.BoxSizer(wx.HORIZONTAL)
		self.ptext = wx.StaticText(self, -1, "Click on the 'Render' button to start the rendering...")
		hsizer.Add(self.ptext, 1, wx.EXPAND|wx.ALL,3)
		self.pnum = wx.StaticText(self,-1, "0 %")
		hsizer.Add(self.pnum, 0, wx.EXPAND|wx.ALL,3)
		import wx.animate
		self.panim = wx.animate.GIFAnimationCtrl(self,-1,"resources/ajax-loader-small.gif")
		# Better to use list of bitmaps and wx.lib.throbber
		hsizer.Add(self.panim, 0, wx.EXPAND|wx.ALL, 3)
		
		vsizer.Add(hsizer, 0, wx.EXPAND|wx.ALL,0)
		
		self.SetSizer(vsizer)
		
	def SetValue(self, value):
		if value == -1:
			self.panim.Stop()
			return
		if self.value == 0 and value != 0:
			self.panim.Show()
			self.panim.Play()
		if value == 0:
			self.panim.Hide()
			self.pnum.Hide()
			self.panim.Stop()
		else:
			self.pnum.SetLabel("%i %" % value)
		self.value = value
		self.g1.SetValue(value)
		
	def SetLabel(self, label):
		self.ptext.SetLabel(label)