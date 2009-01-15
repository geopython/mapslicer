import wx
from gdal2tiles import GDAL2Tiles

# TODO: GetText
from config import _

class wxGDAL2Tiles(GDAL2Tiles):
	
	def setProgressObject(self, progressobject):
		self.progressobject = progressobject
		
	def error(self, msg, details = "" ):
		"""Print an error message and stop the processing"""
		
		self.stop()
		wx.MessageBox(msg, _("Rendering Error"), wx.ICON_ERROR)
		if hasattr(self, 'progressobject'):
			self.progressobject.UpdateRenderText("Rendering Error. Sorry.")
			self.progressobject.UpdateRenderProgress(-1)
		
	# -------------------------------------------------------------------------
	def progressbar(self, complete = 0.0):
		"""Print progressbar for float value 0..1"""
		
		self.progressobject.UpdateRenderProgress(int(complete*100))