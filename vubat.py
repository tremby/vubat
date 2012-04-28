#!/usr/bin/env python

NAME="vubat"
DESCRIPTION="System tray battery status monitor"
AUTHOR = "Simon Ortling, Bart Nagel"
AUTHOR_EMAIL = "krabat@vonuebel.com, bart@tremby.net"
URL = "https://github.com/tremby/vubat"
VERSION = "0.1.1~git"
LICENSE = "GNU GPLv3"
COPYRIGHT_YEAR = "2011"

"""
This program is free software: you can
redistribute it and/or modify it under the terms
of the GNU General Public License as published by
the Free Software Foundation, either version 3 of
the License, or (at your option) any later version.

This program is distributed in the hope that it
will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the
GNU General Public License along with thisprogram.
If not, see <http://www.gnu.org/licenses/>.
"""

import sys, os
import re
import subprocess
import optparse
import datetime
import signal

# gtk modules
import pygtk
pygtk.require("2.0")
import gtk, gobject, glib

# optional modules
try:
	import pynotify
except ImportError:
	print >>sys.stderr, "Install pynotify for notification support"
	pynotify = None

def get_pixmap_dir():
	"""search for status icons"""
	for item in ("/usr/share/pixmaps/vubat",
			"/usr/local/share/pixmaps/vubat",
			"./pixmaps"):
		if os.access(item, os.R_OK):
			return item
PIXMAP_DIR = get_pixmap_dir()

class Status:
	DISCHARGING = 0
	CHARGING = 1
	FULL = 2
	UNKNOWN = 3

	label = {
		DISCHARGING: "Discharging",
		CHARGING: "Charging",
		FULL: "Fully charged",
		UNKNOWN: "Unknown",
	}

class BatteryInfo(object):
	def __init__(self):
		self.status = None
		self.percentage = None
		self.battery_time = None
		self.message = None

class NotAvailableException(Exception):
	pass

class ACPIInfo(BatteryInfo):
	COMMAND = ["acpi", "--battery"]
	SEARCH_PTRN = re.compile("(Unknown|Discharging|Charging|Full)"
			", (\d+)%(?:, (.*))?")

	def __init__(self):
		fail = False
		try:
			p = subprocess.Popen(self.COMMAND, stdout=subprocess.PIPE)
			data = p.communicate()[0]
		except OSError:
			fail = True
		if fail or len(data) == 0 or p.returncode != 0:
			raise NotAvailableException("couldn't get battery info through "
					"acpi")
		super(ACPIInfo, self).__init__()

	def check(self):
		data = subprocess.Popen(self.COMMAND,
				stdout=subprocess.PIPE).communicate()[0].strip().split("\n")[0]
		# FIXME: currently ignoring batteries beyond battery 0
		match = re.search(self.SEARCH_PTRN, data)
		if match is None:
			print >>sys.stderr, "ACPI output didn't match regex: '%s'" % data
		self.percentage = int(match.group(2))
		if match.group(1) == "Discharging":
			self.status = Status.DISCHARGING
		elif match.group(1) == "Charging":
			self.status = Status.CHARGING
		elif match.group(1) == "Full":
			self.status = Status.FULL
		else:
			self.status = Status.UNKNOWN
		self.battery_time = None
		self.message = None
		if match.group(3) is not None:
			try:
				self.battery_time = string_to_timedelta(match.group(3))
			except ValueError:
				self.message = match.group(3)

class IBAMInfo(BatteryInfo):
	RO_CMD = ["ibam", "-sr", "--percentbattery"]
	RW_CMD = ["ibam", "-s", "--percentbattery"]
	SEARCH_PTRN = re.compile("(^[\w|\s]+?:\s*)([\d|:]*)")
	SAMPLE_INTERVAL = 60 # in check turns

	def __init__(self):
		fail = False
		try:
			p = subprocess.Popen(self.RO_CMD, stdout=subprocess.PIPE)
			data = p.communicate()[0]
		except OSError:
			fail = True
		if fail or len(data) == 0 or p.returncode != 0:
			raise NotAvailableException("couldn't get battery info through "
					"ibam")
		self.adapted_time = None
		self.check_count = self.SAMPLE_INTERVAL
		super(IBAMInfo, self).__init__()

	def check(self):
		self.check_count += 1
		if self.check_count >= self.SAMPLE_INTERVAL:
			# check and write sample
			self.check_count = 0
			data = subprocess.Popen(self.RW_CMD,
					stdout=subprocess.PIPE).communicate()[0].strip().split("\n")
		else:
			# check read only
			data = subprocess.Popen(self.RO_CMD,
					stdout=subprocess.PIPE).communicate()[0].strip().split("\n")

		self.percentage, self.battery_time, self.adapted_time = \
				[int(re.search(self.SEARCH_PTRN, x).group(2)) for x in data]

		self.battery_time = string_to_timedelta(self.battery_time)
		self.adapted_time = string_to_timedelta(self.adapted_time)

		if data[1].startswith("Battery"):
			# "Battery time left" -- running on batteries
			self.status = Status.DISCHARGING
		elif data[1].startswith("Charge"):
			# "Charge time left" -- charging up
			self.status = Status.CHARGING
		elif data[1].startswith("Total"):
			# "Total battery time", "Total charge time" -- fully charged
			self.status = Status.FULL
		else:
			self.status = Status.UNKNOWN

class Application:
	def __init__(self):
		try:
			self.info = IBAMInfo()
		except NotAvailableException:
			self.info = ACPIInfo()
		except NotAvailableException:
			print >>sys.stderr, "Couldn't get battery status through IBAM or " \
					"ACPI"
			self.exit(1)
		self.icon = gtk.StatusIcon()
		self.icon.connect("activate", self.on_activate)
		self.icon.connect("popup_menu", self.on_popup_menu)
		self.icon.set_visible(True)
		self.last_status = None
		self.last_pixmap = None
		self.notification = None
		self.critical = False
		self.previously_critical = False
		self.critical_notification_closed = False

	def handle_commandline_arguments(self):
		default_low_mins = 10

		def set_low_percentage(option, opt_str, value, parser):
			num = int(value)
			if num < 0 or num > 100:
				raise optparse.OptionValueError("Low threshold percentage "
						"('%s' given) should be between 0 and 100" % num)
			setattr(parser.values, option.dest, num)

		def set_low_mins(option, opt_str, value, parser):
			num = float(value)
			if num < 0:
				raise optparse.OptionValueError("Low threshold time "
						"('%s' given) should be positive" % num)
			setattr(parser.values, option.dest, num)

		def set_interval(option, opt_str, value, parser):
			num = int(value)
			if num < 0:
				raise optparse.OptionValueError("Interval ('%s' given) should "
						"be positive" % num)
			setattr(parser.values, option.dest, num)

		optionparser = optparse.OptionParser(usage="%prog [options]",
				version="%prog " + VERSION, description="vubat is a standalone "
				"system tray battery status monitor supporting ibam and ACPI "
				"backends, notifications and various other features.", 
				epilog="Send the USR1 signal to the process to force an "
				"update, for instance on an ACPI event. Send the USR2 signal "
				"to force an update and notification even if nothing is new or "
				"important, for instance from a keyboard shortcut.")
		optionparser.add_option("--low-threshold-percentage", 
				dest="low_percentage", type="int", default=None, 
				metavar="PERCENTAGE", action="callback", 
				callback=set_low_percentage, help="The battery "
				"percentage below which a critical warning will be displayed. "
				"Conflicts with --low-threshold-mins.")
		optionparser.add_option("--low-threshold-mins", type="float", 
				dest="low_mins", default=None, metavar="MINS", 
				action="callback", callback=set_low_mins, help="The remaining "
				"battery life in minutes (can be a floating point number) "
				"below which a critical warning will be displayed. Conflicts "
				"with --low-threshold-percentage. Default is %s." % 
				default_low_mins)
		optionparser.add_option("--interval", "-i", type="int", default=5000, 
				metavar="MS", action="callback", callback=set_interval, 
				help="The interval in milliseconds between polls for battery "
				"status (default %default)")
		optionparser.add_option("--initial-notification", "-n", default=False, 
				action="store_true", help="Show a notification as soon as the "
				"program is started (normally this first status is supressed)")

		(self.options, args) = optionparser.parse_args()
		if len(args) != 0:
			optionparser.error("Expected no non-option arguments")
		if self.options.low_percentage is not None and \
				self.options.low_mins is not None:
			optionparser.error("At maximum one of --low-threshold-percentage "
					"and --low-threshold-mins should be used")
		elif self.options.low_percentage is None and \
				self.options.low_mins is None:
			self.options.low_mins = \
					default_low_mins

	def run(self):
		# handle commandline arguments
		self.handle_commandline_arguments()

		# get the inital battery status
		self.update_status(self.options.initial_notification)

		# set up the polling interval
		gobject.timeout_add(self.options.interval, self.update_status)

		# listen for USR1 signal and force an update whenever it's received
		def handle_signal_usr1(*args, **kwargs):
			self.update_status()
		signal.signal(signal.SIGUSR1, handle_signal_usr1)

		# listen for USR2 signal and force an update and notification whenever 
		# it's received
		def handle_signal_usr2(*args, **kwargs):
			self.update_status(True)
		signal.signal(signal.SIGUSR2, handle_signal_usr2)

		# listen for kill signals and exit cleanly
		def handle_exit_signal(*args, **kwargs):
			self.exit(0)
		signal.signal(signal.SIGINT, handle_exit_signal)
		signal.signal(signal.SIGTERM, handle_exit_signal)

		# run the GTK mail loop
		try:
			gtk.main()
		except KeyboardInterrupt:
			pass

	def get_pixmap(self):
		if self.info.status:
			# we are not running on battery
			idx = 5
		else:
			idx = 4
			tmp = 0
			for i in range(4):
				tmp += (i + 1) * 10
				if self.info.percentage <= tmp:
					idx = i + 1
					break
		return "status%d.png" % idx

	def notification_closed_handler(self, n):
		if self.critical:
			self.critical_notification_closed = True

	def below_threshold(self):
		if self.options.low_percentage is not None:
			if self.info.percentage is None:
				return False
			return self.info.percentage <= self.options.low_percentage

		d = self.info.battery_time
		if d is None:
			return False
		return d.days * 24 * 60 + d.seconds / 60.0 <= self.options.low_mins

	def update_status(self, notification=None):
		self.info.check()

		pixmap = self.get_pixmap()
		if self.last_pixmap != pixmap:
			self.icon.set_from_file(os.path.join(PIXMAP_DIR, pixmap))

		self.icon.set_tooltip(self.get_status_string())

		self.critical = self.below_threshold() \
				and self.info.status == Status.DISCHARGING
		if not self.critical:
			self.critical_notification_closed = False

		if notification == True or notification is None and (
				# fresh critical
				self.critical and not self.previously_critical

				# no longer critical
				or not self.critical and self.previously_critical

				# still critical, notification hasn't been closed
				or self.critical and not self.critical_notification_closed

				# status has changed
				or self.last_status != self.info.status):
			self.display_notification()

		self.last_status = self.info.status
		self.last_pixmap = pixmap
		self.previously_critical = self.critical

		return True

	def get_status_string(self):
		havetime = False
		string = "%s\n%d%%" % (Status.label[self.info.status], 
				self.info.percentage)
		try:
			string += "\n%s" % timedelta_to_string(self.info.adapted_time)
			havetime = True
		except AttributeError:
			if self.info.battery_time is not None:
				havetime = True
				string += "\n%s" % timedelta_to_string(self.info.battery_time)
		if havetime:
			if self.info.status == Status.CHARGING:
				string += " until charged"
			elif self.info.status == Status.DISCHARGING:
				string += " remaining"
			elif self.info.status == Status.FULL:
				string += " available"
		if self.info.message is not None:
			string += "\n%s" % self.info.message
		return string

	def on_activate_response(self, widget, response, data=None):
		widget.hide()

	def display_notification(self):
		if pynotify is None:
			return

		if self.critical:
			title = "Low battery"
		else:
			title = "Battery status"

		if self.notification is None:
			pynotify.init(NAME)
			self.notification = pynotify.Notification(title, 
					self.get_status_string(), 
					os.path.abspath(os.path.join(PIXMAP_DIR, 
						self.get_pixmap())))
			if hasattr(self.notification, "attach_to_status_icon"):
				self.notification.attach_to_status_icon(self.icon)
			self.notification.connect("closed", self.notification_closed_handler)
		else:
			self.notification.update(title, self.get_status_string(), 
					os.path.abspath(os.path.join(PIXMAP_DIR, 
						self.get_pixmap())))

		if self.critical:
			self.notification.set_urgency(pynotify.URGENCY_CRITICAL)
			self.notification.set_timeout(pynotify.EXPIRES_NEVER)
		else:
			self.notification.set_urgency(pynotify.URGENCY_NORMAL)
			self.notification.set_timeout(pynotify.EXPIRES_DEFAULT)

		self.notification.show()

	def on_activate(self, icon, data=None):
		self.critical_notification_closed = False
		self.display_notification()

	def on_popup_response(self, widget, response, data=None):
		if response == gtk.RESPONSE_OK:
			self.exit()
		else:
			widget.hide()

	def on_popup_menu(self, icon, button, time):
		menu = gtk.Menu()

		about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
		about.connect("activate", self.show_about_dialog)
		menu.append(about)
		quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		quit.connect("activate", self.exit)
		menu.append(quit)

		menu.show_all()
		menu.popup(None, None, gtk.status_icon_position_menu, button, time, 
				self.icon)

	def show_about_dialog(self, widget):
		about_dialog = gtk.AboutDialog()

		about_dialog.set_destroy_with_parent(True)
		about_dialog.set_name(NAME)
		about_dialog.set_version(VERSION)
		about_dialog.set_logo(gtk.gdk.pixbuf_new_from_file(
				os.path.abspath(os.path.join(PIXMAP_DIR, "vubat.png"))))

		authors = []
		for i, n in enumerate(AUTHOR.split(", ")):
			authors.append(n + " <" + AUTHOR_EMAIL.split(", ")[i] + ">")
		about_dialog.set_authors(authors)

		about_dialog.run()
		about_dialog.destroy()

	def exit(self, *args, **kwargs):
		if self.notification is not None:
			try:
				self.notification.close()
			except glib.GError:
				pass
		gtk.main_quit()
		try:
			code = kwargs.code
		except AttributeError:
			code = 0
		sys.exit(code)

def string_to_timedelta(string):
	match = re.search("(\d+):(\d\d):(\d\d)", string)
	if match is None:
		raise ValueError("no HH:MM:SS string in input '%s'" % string)
	return datetime.timedelta(0, int(match.group(3)), 0, 0, int(match.group(2)), 
			int(match.group(1)))
def timedelta_to_string(delta):
	total_seconds = delta.days * 24 * 3600 + delta.seconds
	h = total_seconds / 3600
	m = (total_seconds - h * 3600) / 60
	return "%d:%02d" % (h, m)

if __name__ == "__main__":
	app = Application()
	app.run()
