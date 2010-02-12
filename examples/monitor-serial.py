#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright (c) 2010 Jean-Baptiste Denis.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 and superior as published by the Free
# Software Foundation.
#
# A copy of the license has been included in the COPYING file.

import sys
import os

try:
    # first we try system wide
    import treewatcher
except ImportError:
    # if it fails, we try it from the project source directory
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.path.pardir))
    import treewatcher


from treewatcher import EventsCallbacks, choose_source_tree_monitor


class MonitorCallbacks(EventsCallbacks):
    """
    Example callbacks which will output the event and path
    This is a serial type callbacks object : they will be
    called in the same process as the monitor.
    """

    def create(self, path, is_dir):
        """ callback called on a 'IN_CREATE' event """
        print "create:", path, is_dir


    def delete(self, path, is_dir):
        """ callback called on a 'IN_DELETE' event """
        print "delete:", path, is_dir


    def close_write(self, path, is_dir):
        """ callback called on a 'IN_CLOSE_WRITE' event """
        print "close_write:", path, is_dir


    def moved_from(self, path, is_dir):
        """ callback called on a 'IN_MOVED_FROM' event """
        print "moved_from:", path, is_dir


    def moved_to(self, path, is_dir):
        """ callback called on a 'IN_MOVED_TO' event """
        print "moved_to:", path, is_dir


    def modify(self, path, is_dir):
        """ callback called on a 'IN_MODIFY' event """
        print "modify:", path, is_dir


    def attrib(self, path, is_dir):
        """ callback called on a 'IN_ATTRIB' event """
        print "attrib:", path, is_dir


    def unmount(self, path, is_dir):
        """ callback called on a 'IN_UNMOUNT' event """
        print "unmount:", path, is_dir


if __name__ == '__main__':
    # Yeah, command line parsing
    if len(sys.argv) < 2:
        print "usage:", sys.argv[0], "directory"
        sys.exit(1)

    # we check if the provided string is a valid directory
    path_to_watch = sys.argv[1]
    if not os.path.isdir(path_to_watch):
        print path_to_watch, "is not a valid directory."
        sys.exit(2)

    # We instanciate our callbacks object
    callbacks = MonitorCallbacks()
    # we get a source tree monitor
    stm = choose_source_tree_monitor()
    # we set our callbacks
    stm.set_events_callbacks(callbacks)
    # we start the monitor
    stm.start()
    # after that, we can add the directory we want to watch
    stm.add_source_dir(path_to_watch)

    print "Watching directory", path_to_watch
    print "Open a new terminal, and create/remove some folders and files in the", path_to_watch, "directory"
    print "Ctrl-C to exit..."

    try:
        # without specific arguments, the next call will block forever
        # open a terminal, and create/remove some folders and files
        # this will last forever. use Ctrl-C to exit.
        stm.process_events()
        # see monitor-timeout-serial.py for an example with a timeout argument
    except KeyboardInterrupt:
        print "Stopping monitor."
    finally:
        # clean stop
        stm.stop()


