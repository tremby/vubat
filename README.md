vubat
=====

ABOUT
-----

vubat is a small system tray battery status monitor written in Python and GTK.

It was originally written by Simon Ortling[1] and forked in 2011 by 
Bart Nagel[2] to add support for ACPI and extra features.

[1]: http://ortling.com/vubat/
[2]: https://github.com/tremby/vubat

REQUIREMENTS
------------

- some version of pygtk
- optionally, pynotify (in Ubuntu this is in the package python-notify), to 
  enable notifications

INSTALLATION
------------

to build:

	python setup.py build

to install to /usr/local (root permissions are required):

	python setup.py install

USAGE
-----

	vubat

no arguments, no parameters, nothing

You may want to put it in your `~/.xinitrc` or other window manager startup 
script backgrounded, like

	vubat &

TODO
----

- fix FIXMEs
