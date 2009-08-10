#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TODO: Cleaning the code, refactoring before 1.0 publishing

import os, sys

# Where is the executable file on the disk?
exepath = os.getcwd()
if hasattr(sys, "frozen") or sys.executable.find('MapTiler.app') != -1:
	exepath = os.path.dirname(sys.executable)

# Windows: set the GDAL and PROJ variables ..
if sys.platform in ['win32','win64'] and not os.environ.has_key('GDAL_DATA'):
	# .. to the local directory in the py2exe distribution
	if os.path.exists(os.path.join( exepath, "gdal" )):
		os.environ['PROJ_LIB'] = os.path.join( exepath, "proj" )
		os.environ['GDAL_DATA'] = os.path.join( exepath, "gdal" )
		os.environ['GDAL_DRIVER_PATH'] = os.path.join( exepath, "gdalplugins" )
	# .. to the OSGeo4W default directories
	elif os.path.exists('C:\\OSGeo4W\\apps\\gdal-16'):
		sys.path.insert(0, 'C:\\OSGeo4W\\apps\\gdal-16\\pymod' )
		os.environ['PATH'] += ';C:\\OSGeo4W\\bin'
		os.environ['PROJ_LIB'] = 'C:\\OSGeo4W\\share\\proj'
		os.environ['GDAL_DATA'] = 'C:\\OSGeo4W\\apps\\gdal-16\\share\\gdal'
		os.environ['GDAL_DRIVER_PATH'] = 'C:\\OSGeo4W\\apps\\gdal-16\\bin\\gdalplugins'
	# otherwise we need to use existing system setup

# Mac: GDAL.framework is in the application bundle or in the /Library/Frameworks
if sys.platform == 'darwin' and not os.environ.has_key('GDAL_DATA'):
	frameworkpath = exepath[:(exepath.find('MapTiler.app')+12)]+'/Contents/Frameworks'
	if not os.path.exists( os.path.join(frameworkpath, "GDAL.framework" )):
		frameworkpath = "/Library/Frameworks"
	os.environ['PROJ_LIB'] = os.path.join( frameworkpath, "PROJ.framework/Resources/proj/" )
	os.environ['GDAL_DATA'] = os.path.join( frameworkpath, "GDAL.framework/Resources/gdal/" )
	os.environ['GDAL_DRIVER_PATH'] = os.path.join( frameworkpath, "GDAL.framework/PlugIns/" )
	sys.path.insert(0, os.path.join( frameworkpath, "GDAL.framework/Versions/Current/Python/site-packages/" ))
	sys.path.insert(0, "/System/Library/Frameworks/Python.framework/Versions/Current/Extras/lib/python/")

# Other systems need correctly installed GDAL libraries

import wx
import maptiler
__version__ = maptiler.version

class MapTilerApp(wx.App):
	
	def OnInit(self):
		wx.InitAllImageHandlers()
		self.main_frame = maptiler.MainFrame(None, -1, "")
		self.SetTopWindow(self.main_frame)
		self.SetAppName("MapTiler")
		return True
		
	def MacOpenFile(self, filename):
		self.main_frame._add(filename)
		
	def Show(self):
		self.main_frame.Show()

if __name__ == "__main__":
	
	# TODO: GetText
	#import gettext
	#gettext.install("maptiler")
	_ = lambda s: s

	# TODO: Parse command line arguments:
	# for both batch processing and initialization of the GUI

	#wx.SystemOptions.SetOptionInt("mac.listctrl.always_use_generic",0)
	app = MapTilerApp(False)

	#spath = wx.StandardPaths.Get()
	#print spath.GetExecutablePath()
	
	try:
		from osgeo import gdal
	except ImportError:
		# TODO: Platform specific error messages - are part of the GUI...
		if sys.platform == 'darwin':
			wx.MessageBox(_("""GDAL 1.6 framework is not found in your system!\n
Please install GDAL framework from the website:
http://www.kyngchaos.com/software:frameworks"""), _("Error: GDAL Framework not found!"), wx.ICON_ERROR)
			import webbrowser
			webbrowser.open_new("http://www.kyngchaos.com/software:frameworks#gdal")
			sys.exit(1)
		elif sys.platform in ['win32','win64']:
			wx.MessageBox(_("""GDAL 1.6 library is not found in your system!\n
If you used the installer then please report this problem as an issue at:
http://code.google.com/p/maptiler/issues"""), _("Error: GDAL library not found!"), wx.ICON_ERROR)
			sys.exit(1)
		elif sys.platform.startswith('linux'):
			wx.MessageBox(_("""GDAL 1.6 library is not found in your system!\n
Please install it as a package in your distribution or from the source code:
http://trac.osgeo.org/gdal/wiki/BuildHints"""), _("Error: GDAL library not found!"), wx.ICON_ERROR)
			sys.exit(1)
		print _("GDAL library not available - please install GDAL and it's python module!")

	app.Show()
	wx.MessageBox(_("""This is a development version of MapTiler application.
It has known bugs and limits.\n
It is not for production use but for testing and preview!"""), _("MapTiler Alpha version (%s)") % __version__, wx.OK | wx.ICON_INFORMATION)
	app.MainLoop()
