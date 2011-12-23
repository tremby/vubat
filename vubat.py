#!/usr/bin/python
# -*- coding: utf-8 -*-

# vubat.py by simon ortling 2008 <krabat at vonuebel dot com>
# version 0.04
# modified to support ACPI by Bart Nagel <bart@tremby.net>, 2011

"""
vubat is an battery status systray frontend.
Copyright (C) 2008 Simon Ortling (aka Krabat vonUebel)
Copyright (C) 2011 Bart Nagel

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

CHECK_INTERVAL = 2000 # in milliseconds
SAMPLE_INTERVAL = 60 # in check turns

IBAM_RO_CMD = "ibam -sr --percentbattery"
IBAM_RW_CMD = "ibam -s --percentbattery"
IBAM_SEARCH_PTRN = re.compile ("(^[\w|\s]+?:\s*)([\d|:]*)")

def get_pixmap_dir ():
    """search for status icons"""
    for item in ("/usr/share/pixmaps/vubat",
        "/usr/local/share/pixmaps/vubat",
        "./pixmaps"):
        if os.access (item, os.R_OK):
            return item
PIXMAP_DIR = get_pixmap_dir ()

class IBAMInfo:
    def __init__ (self):
        self.status = 0
        self.percentage = 0
        self.battery_time = 0
        self.adapted_time = 0
        self.check_count = SAMPLE_INTERVAL

    def check (self):
        self.check_count += 1
        if self.check_count >= SAMPLE_INTERVAL:
            # check and write sample
            self.check_count = 0
            data = os.popen (IBAM_RW_CMD).read ().strip ().split ("\n")
        else:
            # check read only
            data = os.popen (IBAM_RO_CMD).read ().strip ().split ("\n")
        self.percentage, self.battery_time, self.adapted_time = [
            int (re.search (IBAM_SEARCH_PTRN, x).group (2)) for x in data]
        if data [1].startswith ("Battery"):
            self.status = 0
        elif data [1].startswith ("Charge"):
            self.status = 1
        else:
            self.status = 2        

class Application:
    def __init__ (self):
        self.info = IBAMInfo ()
        self.icon = gtk.StatusIcon ()
        #self.icon.connect ("activate", self.on_activate)
        self.icon.connect ("popup_menu", self.on_popup_menu)
        self.icon.set_visible (True)
        self.status_labels = ("Battery", "Charging", "Charged")
        self.last_pixmap = None

    def run (self):
        self.update_status ()
        gtk.main()

    def get_pixmap (self):
        if self.info.status:
            # we are not running on battery
            idx = 5
        else:
            idx = 4
            tmp = 0
            for i in range (4):
                tmp += (i+1)*10
                if self.info.percentage <= tmp:
                    idx = i+1
                    break
        return "status%d.png"%(idx)

    def update_status (self):
        self.info.check ()

        pixmap = self.get_pixmap ()
        if self.last_pixmap != pixmap:
            self.icon.set_from_file (os.path.join (PIXMAP_DIR, pixmap))
            self.last_pixmap = pixmap

        self.icon.set_tooltip ("%s\n%d%%\n%d:%02d"%(
            self.status_labels [self.info.status],
            self.info.percentage, 
            self.info.adapted_time/3600,
            (self.info.adapted_time/60)%60))

        gobject.timeout_add (5000, self.update_status)

    def on_activate_response (self, widget, response, data= None):
        widget.hide ()

    def on_activate (self, button, widget, data=None):
        pass

    def on_popup_response (self, widget, response, data= None):
        if response == gtk.RESPONSE_OK:
            gtk.main_quit ()
        else:
            widget.hide ()

    def on_popup_menu (self, button, widget, data=None):
        dialog = gtk.MessageDialog (parent=None, 
            flags=gtk.DIALOG_DESTROY_WITH_PARENT,
            type=gtk.MESSAGE_INFO,
            buttons=gtk.BUTTONS_OK_CANCEL,
            message_format="Quit?")
        dialog.set_title ("Quit vubat?")
        dialog.connect ("response", self.on_popup_response)
        dialog.show ()


if __name__ == "__main__":
    app = Application ()
    app.run ()
