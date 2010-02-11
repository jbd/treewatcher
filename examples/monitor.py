#-*- coding: utf-8 -*-
#
# Copyright (c) 2010 Jean-Baptiste Denis.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 and superior as published by the Free
# Software Foundation.
#
# A copy of the license has been included in the COPYING file.
#
# This file is HEAVILY inspired by some parts of the pytagsfs project by Forest Bond.
# Please see: http://www.pytagsfs.org/
#
# It has been modified for my specific needs. I don't think those changes could appear
# in pytagsfs.

import sys
import os

try:
    # first we try system wide
    from treewatcher import EventsCallbacks, choose_source_tree_monitor
except ImportError:
    this_file_dirname = os.path.split(os.path.realpath(__file__))[0]
    treewatcher_path = os.path.split(this_file_dirname)[0]
    sys.path.append(treewatcher_path)
    from treewatcher import EventsCallbacks, choose_source_tree_monitor


class MonitorCallbacks(EventsCallbacks):
    """
    Example callbacks which will output the event and path
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
    try:
        # without specific arguments, the next call will block forever
        # open a terminal, and create/remove some folders and files
        stm.process_events()
    except KeyboardInterrupt:
        print "Stopping monitor."
    finally:
        # clean stop
        stm.stop()


