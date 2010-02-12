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


"""
This module contains the test implementing scenarios from
the scenarios.py files.

The tree watcher and the callbacks are in the same process.
"""

import os
import sys

import helper

# see scenerios.py file for comments on this block
try:
    import treewatcher
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.path.pardir))
    import treewatcher


from treewatcher import EventsCallbacks
from scenarios import TestTreeWatcher


class SerialEventsCallbacks(EventsCallbacks):
    """
    We will count events and check if we got
    the right number.

    Callbacks are called in the same process of the tree watcher,
    in a serial way.
    """
    def __init__(self):
        """
        We create the counters for create and close_write events
        Why no property for create and close_write variable ?
        Because i had some problem with them in the threaded code
        case (test_threaded.py)
        """
        EventsCallbacks.__init__(self)
        self.create_counter = 0
        self.cw_counter = 0


    def create(self, path, is_dir):
        """ Impressive function """
        self.create_counter += 1


    def close_write(self, path, is_dir):
        """ Again """
        self.cw_counter += 1


    def get_create_counter(self):
        """
        Getter
        """
        return self.create_counter


    def get_cw_counter(self):
        """
        Getter
        """
        return self.cw_counter

class TestSerialTreeWatcher(TestTreeWatcher):
    """
    Our test class.
    We watch a specified directory, create some particular tree structure in it
    and check if we've got the right number of inotify events.

    Callbacks are called in the same process of the tree watcher,
    in a serial way.

    We just have to implement the setUp function with our callbacks.
    All the tests are in the TestTreeWatcher base class.
    """
    def setUp(self):
        """
        This function is called before each test
        We create and start our tree watcher
        """
        self.setup_helper(callbacks=SerialEventsCallbacks())


# see helper.py file and the tests_runner comments
TESTS_TO_RUN = [ "TestSerialTreeWatcher", ]

if __name__ == "__main__":
    helper.tests_runner(__file__)
