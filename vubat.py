#!/usr/bin/env python

NAME="vubat"
DESCRIPTION="System tray battery status monitor"
AUTHOR = "Simon Ortling, Bart Nagel"
AUTHOR_EMAIL = "krabat@vonuebel.com, bart@tremby.net"
URL = "https://github.com/tremby/vubat"
VERSION = "0.1.0~git"
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

# gtk modules
import pygtk
pygtk.require ('2.0')
import gtk, gobject
try:
	import pynotify
except ImportError:
	print >>sys.stderr, "Install pynotify for notification support"
	pynotify = None

CHECK_INTERVAL = 5000 # in milliseconds
SAMPLE_INTERVAL = 60 # in check turns

IBAM_RO_CMD = "ibam -sr --percentbattery"
ACPI_RO_CMD = "acpi -b"
ACPI_SEARCH_PTRN = re.compile("(Unknown|Discharging|Charging|Full), (\d+)%(?:, (.*))?")
IBAM_RW_CMD = "ibam -s --percentbattery"
IBAM_SEARCH_PTRN = re.compile("(^[\w|\s]+?:\s*)([\d|:]*)")

LOW_THRESHOLD = 10

acpi = True # FIXME: autodetect

def get_pixmap_dir():
	"""search for status icons"""
	for item in ("/usr/share/pixmaps/vubat",
			"/usr/local/share/pixmaps/vubat",
			"./pixmaps"):
		if os.access(item, os.R_OK):
			return item
PIXMAP_DIR = get_pixmap_dir()

class ACPIInfo:
	def __init__(self):
		self.status = 0
		self.percentage = 0
		self.battery_time = 0

	def check(self):
		data = os.popen(ACPI_RO_CMD).read().strip().split("\n")[0] # FIXME: currently ignoring batteries beyond battery 0
		match = re.search(ACPI_SEARCH_PTRN, data)
		if match is None:
			print >>sys.stderr, "ACPI output didn't match regex: '%s'" % data
		self.percentage = int(match.group(2))
		if match.group(1) == "Discharging":
			self.status = 0
		elif match.group(1) == "Charging":
			self.status = 1
		elif match.group(1) == "Full":
			self.status = 2
		else:
			self.status = 3
		self.battery_time = match.group(3)

class IBAMInfo:
	def __init__(self):
		self.status = 0
		self.percentage = 0
		self.battery_time = 0
		self.adapted_time = 0
		self.check_count = SAMPLE_INTERVAL

	def check(self):
		self.check_count += 1
		if self.check_count >= SAMPLE_INTERVAL:
			# check and write sample
			self.check_count = 0
			data = os.popen(IBAM_RW_CMD).read().strip().split("\n")
		else:
			# check read only
			data = os.popen(IBAM_RO_CMD).read().strip().split("\n")

		self.percentage, self.battery_time, self.adapted_time = [ 
				int(re.search(IBAM_SEARCH_PTRN, x).group(2)) for x in data]

		if data[1].startswith("Battery"):
			self.status = 0
		elif data[1].startswith("Charge"):
			self.status = 1
		else:
			self.status = 2

class Application:
	def __init__(self):
		self.info = ACPIInfo() if acpi else IBAMInfo()
		self.icon = gtk.StatusIcon()
		self.icon.connect("activate", self.on_activate)
		self.icon.connect("popup_menu", self.on_popup_menu)
		self.icon.set_visible(True)
		self.status_labels =("Discharging", "Charging", "Charged", "Unknown")
		self.last_status = None
		self.last_pixmap = None
		self.last_percentage = None
		if pynotify is not None:
			self.critical_notification = None
			self.critical_notification_closed = False
			pynotify.init(NAME)

	def run(self):
		self.update_status(False)
		gobject.timeout_add(CHECK_INTERVAL, self.update_status)
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

	def critical_notification_closed_handler(self, n):
		print "closed handler" # FIXME: this never happens!
		self.critical_notification_closed = True

	def update_status(self, notification=True):
		self.info.check()

		pixmap = self.get_pixmap()
		if self.last_pixmap != pixmap:
			self.icon.set_from_file(os.path.join(PIXMAP_DIR, pixmap))

		self.icon.set_tooltip(self.get_status_string())

		if notification and pynotify is not None:
			if self.critical_notification is not None:
				n = self.critical_notification
				if self.info.status == 1 or self.info.status == 2 \
						or self.info.percentage > LOW_THRESHOLD:
					# doesn't matter any more -- replace with normal 
					# notification
					n.close()
					self.critical_notification = None
					self.critical_notification_closed = False
					self.display_notification()
				elif not self.critical_notification_closed:
					# it has not been manually closed -- update it
					n.update("Low battery", self.get_status_string(), 
							os.path.abspath(os.path.join(PIXMAP_DIR, 
								self.get_pixmap())))
					n.show()
			elif self.info.percentage <= LOW_THRESHOLD and (
					self.last_percentage > LOW_THRESHOLD
					or self.info.status == 0 and self.last_status != 0):
				# display critical notification
				n = self.critical_notification = pynotify.Notification(
						"Battery low", self.get_status_string(), 
						os.path.abspath(os.path.join(PIXMAP_DIR, 
							self.get_pixmap())))
				n.set_urgency(pynotify.URGENCY_CRITICAL)
				n.set_timeout(pynotify.EXPIRES_NEVER)
				#print gobject.signal_list_names(n)
				n.connect("closed", self.critical_notification_closed_handler)
				n.show()
			elif self.last_status != self.info.status:
				self.display_notification()

		self.last_status = self.info.status
		self.last_pixmap = pixmap
		self.last_percentage = self.info.percentage

		return True

	def get_status_string(self):
		status = "%s\n%d%%" % (self.status_labels[self.info.status], 
				self.info.percentage)
		try:
			status += "\n%d:%02d" % (self.info.adapted_time / 3600, 
					(self.info.adapted_time / 60) % 60)
		except AttributeError:
			if self.info.battery_time is not None:
				status += "\n%s" % self.info.battery_time
		return status

	def on_activate_response(self, widget, response, data=None):
		widget.hide()

	def display_notification(self):
		if pynotify is not None:
			notification = pynotify.Notification("Battery status", 
					self.get_status_string(), 
					os.path.abspath(os.path.join(PIXMAP_DIR, 
						self.get_pixmap())))
			notification.show()

	def on_activate(self, icon, data=None):
		self.display_notification()

	def on_popup_response(self, widget, response, data=None):
		if response == gtk.RESPONSE_OK:
			gtk.main_quit()
		else:
			widget.hide()

	def on_popup_menu(self, icon, button, time):
		menu = gtk.Menu()

		about = gtk.MenuItem("About")
		about.connect("activate", self.show_about_dialog)
		menu.append(about)
		quit = gtk.MenuItem("Quit")
		quit.connect("activate", gtk.main_quit)
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

if __name__ == "__main__":
	app = Application()
	app.run()
