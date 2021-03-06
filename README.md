vubat
=====

About
-----

vubat is a small system tray battery status monitor written in Python and GTK.

It was originally written by [Simon Ortling][1] and forked in 2011 by 
[Bart Nagel][2] to add support for ACPI, notifications and other extra features.

[1]: http://ortling.com/vubat/
[2]: https://github.com/tremby/vubat

The tray icon is coloured according to the battery's status:

- Blue when battery is charging or charged
- Green when battery is discharging anywhere down to 60%
- Yellow when battery is discharging anywhere down to 30%
- Orange when battery is discharging anywhere down to 10%
- Red when battery is low

Requirements
------------

- Some version of pygtk
- Optionally, pynotify (in Ubuntu this is in the package python-notify), to 
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

For a list of options use the `--help` switch:

	vubat --help

You may want to put it in your `~/.xinitrc` or other window manager startup 
script backgrounded, like

	vubat &

To force vubat to update you can send it the `USR1` signal, for instance on ACPI 
events so that the status is updated promptly.

	killall -USR1 vubat

Or to force a notification to appear even if nothing is new or important you can 
send the `USR2` signal.

TODO
----

- Fix FIXMEs
- Test in ibam (ibam doesn't work on my laptop) or remove support
