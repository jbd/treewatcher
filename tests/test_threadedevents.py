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

The tree watcher and the callbacks are in different threads.
The callbacks themself can be in different threads too.
"""

import os
import sys
import threading

import helper

# see scenerios.py file for comments on this block
try:
    import treewatcher 
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.path.pardir))
    import treewatcher

from treewatcher import ThreadedEventsCallbacks
from scenarios import TestTreeWatcher


class ThreadedTestsCallbacks(ThreadedEventsCallbacks):
    """
    We will count events and check if we got
    the right number

    The tree watcher and the callbacks are in different threads.
    The callbacks themself can be in different threads too.
    """
    def __init__(self):
        """
        We create the counters for create and close_write events
        Why no property for create and close_write variable ?
        Because i had some problem with them. The setter and getter
        of the variables were protected using locks, but the results 
        was corrupted. I didn't manage to find why.

        Since we have a shared state and the callbacks can be called from
        differents threads, we must protect the counter using locks.
        """
        ThreadedEventsCallbacks.__init__(self)
        self.cc_lock = threading.Lock()
        self.cw_lock = threading.Lock()
        self.create_counter = 0
        self.cw_counter = 0


    def create(self, path, is_dir):
        """ Impressive function """
        self.cc_lock.acquire()
        self.create_counter += 1
        self.cc_lock.release()


    def close_write(self, path, is_dir):
        """ Again """
        self.cw_lock.acquire()
        self.cw_counter += 1
        self.cw_lock.release()


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


class TestOneThreadTreeWatcher(TestTreeWatcher):
    """
    Our test class.
    We watch a specified directory, create some particular tree structure in it
    and check if we've got the rigght number of inotify events

    The tree watcher and the callbacks are in different threads.
    In this case, the tree watcher is in its own thread, and the 
    callbacks are in only one thread

    We just have to implement the setUp function with our callbacks.
    All the tests are in the TestTreeWatcher base class.
    """
    def setUp(self):
        """
        This function is called before each test
        We create and start our tree watcher
        """
        self.setup_helper(callbacks=ThreadedTestsCallbacks(), workers=1)


class TestTwoThreadsTreeWatcher(TestTreeWatcher):
    """
    Same as TestOneThreadTreeWatcher, but the callbacks can
    be called from two threads.
    """
    def setUp(self):
        """
        This function is called before each test
        We create and start our tree watcher
        """
        self.setup_helper(callbacks=ThreadedTestsCallbacks(), workers=2)


class TestFourThreadsTreeWatcher(TestTreeWatcher):
    """
    Same as TestOneThreadTreeWatcher, but the callbacks can
    be called from four threads.
    """
    def setUp(self):
        """
        This function is called before each test
        We create and start our tree watcher
        """
        self.setup_helper(callbacks=ThreadedTestsCallbacks(), workers=4)


class TestEightThreadsTreeWatcher(TestTreeWatcher):
    """
    Same as TestOneThreadTreeWatcher, but the callbacks can
    be called from eight threads.
    """
    def setUp(self):
        """
        This function is called before each test
        We create and start our tree watcher
        """
        self.setup_helper(callbacks=ThreadedTestsCallbacks(), workers=8)


# see helper.py file and the tests_runner comments
TESTS_TO_RUN = [ \
                 "TestOneThreadTreeWatcher", \
                 "TestTwoThreadsTreeWatcher", \
                 "TestFourThreadsTreeWatcher", \
                 "TestEightThreadsTreeWatcher" \
               ]

if __name__ == "__main__":
    helper.tests_runner(__file__)
