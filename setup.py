#!/usr/bin/env python
# -*- coding: utf-8 -*-

# setup.py for vugst by simon ortling 2008 <krabat at vonuebel dot com>

"""
    vubat is an ibam systray frontend.
    Copyright (C) 2008 Simon Ortling (aka Krabat vonUebel)

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

setup (
    name="vubat",
    version="0.01",
    description="System tray frontend to IBAM",

    author="simon@ortling (aka Krabat vonUebel)",
    author_email="krabat at vonuebel dot com",
    url="http://sourceforge.net/projects/vubat/",

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

#    classifiers=[
#          "Development Status :: 3 - Alpha",
#          "Environment :: X Window System (X11)",
#          "Environment :: GTK+",
#          "Intended Audience :: End Users/Desktop",
#          "License :: GNU General Public License (GPL)"
#          "Operating System :: Linux",
#          "Operating System :: All POSIX (Linux/BSD/UNIX-like OSes)",
#          "Programming Language :: Python",
#          ],
)
