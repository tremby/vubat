vubat
=====

About
-----

vubat is a small system tray battery status monitor written in Python and GTK.

It was originally written by [Simon Ortling][1] and forked in 2011 by 
[Bart Nagel][2] to add support for ACPI and extra features.

[1]: http://ortling.com/vubat/
[2]: https://github.com/tremby/vubat

The tray icon is coloured according to the battery's status:

- red when battery is discharging and below 10%
- orange when battery is discharging and up to 30%
- yellow when battery is discharging and up to 60%
- green when battery is discharging and up to 100%
- blue when battery is charging or charged

Requirements
------------

- some version of pygtk
- optionally, pynotify (in Ubuntu this is in the package python-notify), to 
  enable notifications

Installation
------------

It's possible to just run it from the working directory with no further steps, 
by running the `vubat` script.

To build:

	python setup.py build

To install to /usr/local (root permissions are required):

	python setup.py install

Usage
-----

	vubat

no arguments, no parameters, nothing

You may want to put it in your `~/.xinitrc` or other window manager startup 
script backgrounded, like

	vubat &

TODO
----

- fix FIXMEs
