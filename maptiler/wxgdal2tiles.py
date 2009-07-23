import wx
from gdal2tiles import GDAL2Tiles

# TODO: GetText
from config import _

UPDATE_PROGRESS_EVENT = wx.NewEventType()
EVT_UPDATE_PROGRESS = wx.PyEventBinder(UPDATE_PROGRESS_EVENT, 0)

class UpdateProgressEvent(wx.PyEvent):
	def __init__(self, progress):
		wx.PyEvent.__init__(self)
		self.SetEventType(UPDATE_PROGRESS_EVENT)
		self.progress = progress

class wxGDAL2Tiles(GDAL2Tiles):

	def setEventHandler(self, eventHandler):
		self.eventHandler = eventHandler

	def error(self, msg, details = "" ):
		"""Print an error message and stop the processing"""
		
		self.stop()
		wx.MessageBox(msg, _("Rendering Error"), wx.ICON_ERROR)
		if hasattr(self, 'eventHandler'):
			wx.PostEvent(self.eventHandler, 
						 GenericGuiEvent("Rendering Error. Sorry.")
			)
			wx.PostEvent(self.eventHandler,
						 UpdateProgressEvent(-1)
			)

	# -------------------------------------------------------------------------
	def progressbar(self, complete = 0.0):
		"""Print progressbar for float value 0..1"""

		if hasattr(self, 'eventHandler'):
			wx.PostEvent(self.eventHandler, 
						 UpdateProgressEvent(int(complete*100))
			)