#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TODO: Cleaning the code, refactoring before 1.0 publishing

import os, sys

import wx
import maptiler

__version__ = maptiler.version

# Under Windows set the GDAL variables to local directories
# Other systems need correctly installed GDAL libraries
if sys.platform in ['win32','win64']:
	os.environ['GDAL_DATA'] = os.path.join( sys.path[0], "gdaldata" )
	os.environ['GDAL_DRIVER_PATH'] = os.path.join( sys.path[0], "gdalplugins" )

class MapTilerApp(wx.App):
	
	def OnInit(self):
		wx.InitAllImageHandlers()
		self.main_frame = maptiler.MainFrame(None, -1, "")
		self.SetTopWindow(self.main_frame)
		return True
		
	def MacOpenFile(self, filename):
		self.main_frame._add(filename)
		
	def Show(self):
		self.main_frame.Show()

if __name__ == "__main__":
	
	# TODO: GetText
	#import gettext
	#gettext.install("maptiler")

	# TODO: Parse command line arguments:
	# for both batch processing and initialization of the GUI

	#wx.SystemOptions.SetOptionInt("mac.listctrl.always_use_generic",0)
	#app = MapTilerApp(False)
	app = MapTilerApp()
	
	try:
		from osgeo import gdal
	except ImportError:
		# TODO: Platform specific error messages - are part of the GUI...
		if sys.platform == 'darwin':
			wx.MessageBox("""GDAL 1.6 framework is not found in your system!\n
Please install GDAL framework from the website:
http://www.kyngchaos.com/software:frameworks""", "Error: GDAL Framework not found!", wx.ICON_ERROR)
			sys.exit(1)
		elif sys.platform in ['win32','win64']:
			wx.MessageBox("""GDAL 1.6 library is not found in your system!\n
If you used installer then please report this problem as issue at:
http://code.google.com/p/maptiler/issues""", "Error: GDAL library not found!", wx.ICON_ERROR)
			sys.exit(1)
		elif sys.platform == 'linux':
			wx.MessageBox("""GDAL 1.6 library is not found in your system!\n
Please install it as a package in your distribution or from the source code:
http://trac.osgeo.org/gdal/wiki/BuildHints""", "Error: GDAL library not found!", wx.ICON_ERROR)
			sys.exit(1)
		print "GDAL library not available - please install GDAL and it's python module!"

	app.Show()
	app.MainLoop()