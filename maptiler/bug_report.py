
import os
import config
import pprint
import smtplib
import string
import wx
import platform

import email
import email.mime.text
import email.iterators
import email.generator
import email.utils
from email.mime.text import MIMEText

from osgeo import gdal

#TODO: GetText
from config import _


# Settings for email sending.
SMTP_SERVER = "aspmx.l.google.com"
TO_ADDRESS = "bugs@maptiler.com"
FROM_ADDRESS = "bug_reporter@maptiler.com"


def do_bug_report_dialog(parent, back_trace, step):

	"""Show a dialog with bug report form and if user clicks YES, send it."""

	info = state_info(step)
	bug_report = back_trace + "\n\n" + 30*"=" + "\n\n" + info

	dialog = BugReportDialog(parent)
	dialog.set_bug_report(bug_report)

	status = dialog.ShowModal()
	address, message = dialog.get_address_and_message()
	dialog.Destroy()

	if status == wx.ID_OK:
		try:
			send_bug_report(address, message, bug_report)
		except Exception, e:
			wx.MessageBox(_("Sending of bug report failed:\n\n") + str(e), _("Send failed"), wx.ICON_ERROR)
		else:
			wx.MessageBox(_("Bug report was sent."), _("Send successful"))


class BugReportDialog(wx.Dialog):

	"""Allow user to fill in details of bug report.
	
	Dialog with two editable input fields for email address and message text
	and one control which shows collected bug report information.
	"""

	controls = [
		("Your email (optional):", {
			"name" : "address",
			"size" : wx.Size(450, -1)
		}),

		("Your message (optional):", {
			"name"  : "message",
			"size"  : wx.Size(450, 150),
			"style" : wx.TE_MULTILINE,
		}),

		("Information that will be sent:", {
			"name"  : "bug_report",
			"size"  : wx.Size(450, 250),
			"style" : wx.TE_MULTILINE | wx.TE_READONLY
		})
	]

	def __init__(self, *args, **kwargs):
		wx.Dialog.__init__(self, *args, **kwargs)

		self.v_sizer = wx.BoxSizer(wx.VERTICAL)
		self.h_sizer = wx.BoxSizer(wx.HORIZONTAL)

		self.v_sizer.AddSpacer((0, 4))

		for caption, text_options in self.controls:
			self.v_sizer.Add(wx.StaticText(self, label=caption))
			self.v_sizer.AddSpacer((0, 4))
			self.v_sizer.Add(wx.TextCtrl(self, **text_options))
			self.v_sizer.AddSpacer((0, 8))

		self.v_sizer.Add(self.CreateSeparatedButtonSizer(wx.OK | wx.CANCEL), 0, wx.EXPAND)
		self.v_sizer.AddSpacer((0, 4))

		self.h_sizer.AddSpacer((4, 0))
		self.h_sizer.Add(self.v_sizer)
		self.h_sizer.AddSpacer((4, 0))

		self.SetSizer(self.h_sizer)
		self.h_sizer.Fit(self)

	def set_bug_report(self, bug_report):
		self.FindWindowByName("bug_report").SetValue(bug_report)

	def get_address_and_message(self):
		address = self.FindWindowByName("address").GetValue()
		message = self.FindWindowByName("message").GetValue()
		return address, message


def send_bug_report(address, message, bug_report):

	"""Send a bug report by email."""

	body = ("From: %s\n\n %s\n\n" % (address, message)) + 30*"=" + "\n\n" +  bug_report

	email = MIMEText(asciify(body))
	email["Subject"] = "MapTiler bug report"
	email["From"] = FROM_ADDRESS
	email["To"] = TO_ADDRESS

	server = smtplib.SMTP(SMTP_SERVER)
	server.sendmail(FROM_ADDRESS, TO_ADDRESS, email.as_string())
	server.quit()


# Fields of the `config' module that are added into bug report.
CONFIG_FIELDS = [
	"profile","srs","tminz","tmaxz","format","google","openlayers",
	"kml","nodata","url","googlekey","yahookey","files","outputdir"
]


def state_info(step):

	"""Return string with information about the state of configuration and input dataset."""

	s = ("platform = %s\n\nnumber of CPUs = %d\n\npython = %s\n\nstep = %d\n\n"
	        % (platform.platform(), get_ncpus(), platform.python_version(), step))

	d = {}
	for field in CONFIG_FIELDS:
		try:
			d[field] = config.__getattribute__(field)
		except AttributeError:
			pass

	s += "config = \\\n" + pprint.pformat(d)

	if len(config.files) != 0:
		ds = gdal.Open(config.files[0][2], gdal.GA_ReadOnly)
		if ds is None:
			s += "\n\nGDAL can not open the input dataset!"
		else:
			info = dataset_info(ds)
			s += "\n\ndataset = \\\n" + pprint.pformat(info)

	return s


def dataset_info(ds):

	"""Return dictionary of important dataset information."""

	info = {
		"description"     : ds.GetDescription(),
		"driver name"     : ds.GetDriver().ShortName,
		"size"            : (ds.RasterXSize, ds.RasterYSize),
		"projection"      : ds.GetProjection(),
		"geotransform"    : ds.GetGeoTransform(),
		"GCPs"            : [(g.GCPX, g.GCPY, g.GCPPixel, g.GCPLine) for g in ds.GetGCPs()],
		"file list"       : ds.GetFileList(),
		"metadata"        : ds.GetMetadata_List()
	}

	for i in range(ds.RasterCount):
		rb = ds.GetRasterBand(i+1)
		info["band %d" % (i+1)] = raster_band_info(rb)

	return info


def raster_band_info(rb):

	"""Return dictionary of important raster band information."""

	info = {
		"size"                 : (rb.XSize, rb.YSize),
		"data type"            : rb.DataType,
		"block size"           : rb.GetBlockSize(),
		"color interpretation" : gdal_color_interpretation_str[rb.GetRasterColorInterpretation()],
		"metadata"             : rb.GetMetadata_List(),
		"nodata"               : rb.GetNoDataValue()
		# "arbitrary overviews"  : rb.HasArbitraryOverviews()
	}

	for i in range(rb.GetOverviewCount()):
		info["overview %d" % i] = raster_band_info(rb.GetOverview(i))

	return info


# Map GDAL color interpretation enum to human readable strings.
try:
	gdal_color_interpretation_str = {
		gdal.GCI_AlphaBand      : "alpha",
		gdal.GCI_BlackBand      : "black",
		gdal.GCI_BlueBand       : "blue",
		gdal.GCI_CyanBand       : "cyan",
		gdal.GCI_GrayIndex      : "gray index",
		gdal.GCI_GreenBand      : "green",
		gdal.GCI_HueBand        : "hue",
		gdal.GCI_LightnessBand  : "lightness",
		gdal.GCI_MagentaBand    : "magenta",
		gdal.GCI_PaletteIndex   : "palette index",
		gdal.GCI_RedBand        : "red",
		gdal.GCI_SaturationBand :"saturation",
		gdal.GCI_Undefined      : "undefined",
		gdal.GCI_YCbCr_CbBand   : "Cb",
		gdal.GCI_YCbCr_CrBand   : "Cr",
		gdal.GCI_YCbCr_YBand    : "Y",
		gdal.GCI_YellowBand     : "yellow"
	}
except:
	gdal_color_interpretation_str = [
		"undefined","gray index","palette index","red","green","blue","alpha","hue","saturation",
		"lightness","cyan","magenta","yellow","black","Y","Cb","Cr","undefined-max"
	]


# copied from Parallel Python
def get_ncpus():

	"""Detects the number of effective CPUs in the system."""

	# for Linux, Unix and MacOS
	if hasattr(os, "sysconf"):
		if "SC_NPROCESSORS_ONLN" in os.sysconf_names:
			# Linux and Unix
			ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
			if isinstance(ncpus, int) and ncpus > 0:
				return ncpus
		else:
			# MacOS X
			return int(os.popen2("sysctl -n hw.ncpu")[1].read())

	# for Windows
	if "NUMBER_OF_PROCESSORS" in os.environ:
		ncpus = int(os.environ["NUMBER_OF_PROCESSORS"])
		if ncpus > 0:
			return ncpus

	# default value
	return 1


# Emails should not contain non-ASCII characters, lest they
# are marked as spam.
valid_ascii = string.ascii_letters + string.digits + string.punctuation + string.whitespace


def asciify(s):

	"""Return string with non-ASCII characters replaced with ?"""

	def replace(c):
		if c in valid_ascii:
			return c
		else:
			return "?"

	return "".join(replace(c) for c in s)
