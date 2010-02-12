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
import logging
import threading

try:
    # first we try system wide
    import treewatcher
except ImportError:
    # if it fails, we try it from the project source directory
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.path.pardir))
    import treewatcher


from treewatcher import ThreadedEventsCallbacks, choose_source_tree_monitor

_LOGGER = logging.getLogger('_LOGGER')
_LOGGER.setLevel(logging.INFO)
_LOGGER.addHandler(logging.StreamHandler())

class MonitorCallbacks(ThreadedEventsCallbacks):
    """
    Example callbacks which will output the event and path
    This is a threaded type callbacks object : they will be
    called from a different thread of the monitor.

    We need to use logging here to prevent messy output.
    You need to protect shared state from concurrent access
    using Lock for example
    """

    def create(self, path, is_dir):
        """ callback called on a 'IN_CREATE' event """
        _LOGGER.info("create: %s %s %s" % (path, is_dir, threading.current_thread().name))


    def delete(self, path, is_dir):
        """ callback called on a 'IN_DELETE' event """
        _LOGGER.info("delete: %s %s %s" % (path, is_dir, threading.current_thread().name))


    def close_write(self, path, is_dir):
        """ callback called on a 'IN_CLOSE_WRITE' event """
        _LOGGER.info("close_write: %s %s %s" % (path, is_dir, threading.current_thread().name))


    def moved_from(self, path, is_dir):
        """ callback called on a 'IN_MOVED_FROM' event """
        _LOGGER.info("moved_from: %s %s %s" % (path, is_dir, threading.current_thread().name))


    def moved_to(self, path, is_dir):
        """ callback called on a 'IN_MOVED_TO' event """
        _LOGGER.info("moved_to: %s %s %s" % (path, is_dir, threading.current_thread().name))


    def modify(self, path, is_dir):
        """ callback called on a 'IN_MODIFY' event """
        _LOGGER.info("modify: %s %s %s" % (path, is_dir, threading.current_thread().name))


    def attrib(self, path, is_dir):
        """ callback called on a 'IN_ATTRIB' event """
        _LOGGER.info("attrib: %s %s %s" % (path, is_dir, threading.current_thread().name))


    def unmount(self, path, is_dir):
        """ callback called on a 'IN_UNMOUNT' event """
        _LOGGER.info("unmount: %s %s %s" % (path, is_dir, threading.current_thread().name))


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
    # we will use two threads to handle callbacks
    stm.set_workers_number(2)
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


