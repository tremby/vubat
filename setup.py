#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    vubat is a battery status systray frontend.
    Copyright (C) 2008 Simon Ortling (aka Krabat vonUebel)
    Copyright (C) 2011 Bart Nagel

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from distutils.core import setup
import vubat

setup (
    name=vubat.NAME,
    version=vubat.VERSION,
    description=vubat.DESCRIPTION,

    author=vubat.AUTHOR,
    author_email=vubat.AUTHOR_EMAIL,
    url=vubat.URL,
    license=vubat.LICENSE

    py_modules=["vubat", ],
    #requires=["pygtk>=2.0", ],
    scripts=["vubat", ],
    data_files=[("share/pixmaps/vubat", [
        "pixmaps/vubat.png",
        "pixmaps/status1.png",
        "pixmaps/status2.png",
        "pixmaps/status3.png",
        "pixmaps/status4.png",
        "pixmaps/status5.png",
        ]),],
