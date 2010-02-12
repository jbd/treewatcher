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
!!! DOES NOT WORK ! That's why TESTS_TO_RUN is empty. !!!

This module contains the test implementing scenarios from
the scenarios.py files.

The tree watcher and the callbacks are in different processes.
The callbacks themself can be in different processes too.
"""


import os
import sys
import multiprocessing

import helper

# see scenerios.py file for comments on this block
try:
    import treewatcher
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.path.pardir))
    import treewatcher

from treewatcher import MultiProcessingEventsCallbacks
from scenarios import TestTreeWatcher


class MultiProcessingTestsCallbacks(MultiProcessingEventsCallbacks):
    """
    !!! DOES NOT WORK the way i want. TESTS_TO_RUN is empty to reflect that :)!!!
    We will count events and check if we got
    the right number

    The tree watcher and the callbacks are in different processes.
    The callbacks themself can be in different processes too.
    """
    def __init__(self):
        """
        We create the counters for create and close_write events

        Since we have a shared state and the callbacks can be called from
        differents processes, we must protect the counter using adequate object.
        """
        MultiProcessingEventsCallbacks.__init__(self)
        self.create_counter = multiprocessing.Value('I', 0)
        self.cw_counter = multiprocessing.Value('I', 0)


    def create(self, path, is_dir):
        """ Impressive function """
        self.create_counter.value += 1

    def close_write(self, path, is_dir):
        """ Again """
        self.cw_counter.value += 1

    def get_create_counter(self):
        """ Getter """
        return self.create_counter.value

    def get_cw_counter(self):
        """ Getter """
        return self.cw_counter.value


class TestOneProcessTreeWatcher(TestTreeWatcher):
    """
    Our test class.
    We watch a specified directory, create some particular tree structure in it
    and check if we've got the rigght number of inotify events

    The tree watcher and the callbacks are in different processes.
    In this case, the tree watcher is in its own processe, and the 
    callbacks are in only one processe.

    We just have to implement the setUp function with our callbacks.
    All the tests are in the TestTreeWatcher base class.
    """
    def setUp(self):
        """
        This function is called before each test
        We create and start our tree watcher
        """
        self.setup_helper(callbacks=MultiProcessingTestsCallbacks(), workers=1)


class TestTwoProcessesTreeWatcher(TestTreeWatcher):
    """
    Same as TestOneProcessTreeWatcher, but the callbacks can
    be called from two processes.
    """
    def setUp(self):
        """
        This function is called before each test
        We create and start our tree watcher
        """
        self.setup_helper(callbacks=MultiProcessingTestsCallbacks(), workers=2)


class TestFourProcessesTreeWatcher(TestTreeWatcher):
    """
    Same as TestOneProcessTreeWatcher, but the callbacks can
    be called from four processes.
    """
    def setUp(self):
        """
        This function is called before each test
        We create and start our tree watcher
        """
        self.setup_helper(callbacks=MultiProcessingTestsCallbacks(), workers=4)


class TestEightProcessesTreeWatcher(TestTreeWatcher):
    """
    Same as TestOneProcessTreeWatcher, but the callbacks can
    be called from eight processes.
    """
    def setUp(self):
        """
        This function is called before each test
        We create and start our tree watcher
        """
        self.setup_helper(callbacks=MultiProcessingTestsCallbacks(), workers=8)



# no tests to run for the moment
# DOES NOT WORK THE WAY I WANT
TESTS_TO_RUN = [
                 #"TestOneProcessTreeWatcher", \
                 #"TestTwoProcessesTreeWatcher", \
                 #"TestFourProcessesTreeWatcher", \
                 #"TestEightProcessesTreeWatcher"
                 ]

if __name__ == "__main__":
    helper.tests_runner(__file__)

