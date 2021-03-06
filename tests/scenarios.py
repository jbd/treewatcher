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


"""
This module contains all the test scenarios in a base class.
The same tests can be run for different treewatcher type
(serial, threaded)
"""

import os
import sys
import shutil
import unittest
import tempfile
import logging

try:
    # first we try system wide
    import treewatcher
except ImportError:
    # it it fails, it means that the library is not installed.
    # this is a hack to allow running tests without reinstalling the library
    # each time there is a change
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.path.pardir))
    import treewatcher

from treewatcher import choose_source_tree_monitor
from treewatcher import EventsCallbacks


# global logger for this module
_TESTS_LOGGER = logging.getLogger('_TESTS_LOGGER')
_TESTS_LOGGER.setLevel(logging.INFO)
_TESTS_LOGGER.addHandler(logging.StreamHandler())


def create_files(where, files_number=0, dirs_number=0):
    """
    This function will create files in the 'where' directory.
    It's behaviour depends on the value of the dirs_number parameter
    - if dirs_number is 0 (default), number designates the number of files
    which will be created in the where directory.
    - if dirs_number is not 0, dirs_number folders will be created with 'number' files
      in each of them
    """
    if dirs_number == 0:
        for i in range(files_number):
            myfile = tempfile.mkstemp(prefix=('%02d' % i + '_'), dir=where)
            os.close(myfile[0])
    else:
        for i in range(dirs_number):
            location = tempfile.mkdtemp(prefix=('%02d' % i + '_'), dir=where)
            for j in range(files_number):
                myfile = tempfile.mkstemp(prefix=('%02d' % j + '_'), dir=location)
                os.close(myfile[0])


def create_files_tree(where, files_number=0, dirs_number=0, sublevels=0):
    """
    create_file wrapper with a sublevels option. It will create a "create_files" structure
    under each sublevels
    """
    if sublevels == 0:
        create_files(where, files_number, dirs_number)
    else:
        location = where
        for i in range(sublevels):
            location = tempfile.mkdtemp(prefix=('%02d' % i + '_'), dir=location)
            create_files(location, files_number, dirs_number)


def clean_dir(folder):
    """
    Remove the content of 'dir'
    """
    for myfile in os.listdir(folder):
        path = os.path.join(folder, myfile)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(os.path.join(folder, myfile))


def _wanted_close_write(files_number, dirs_number, sublevels, loop):
    """
    Helper function to compute the wanted number of close_write events
    """

    # hack to prevent ugly if/else branching mess
    if sublevels == 0:
        sublevels = 1
    if dirs_number == 0:
        dirs_number = 1
    if loop == 0:
        loop = 1

    return files_number * dirs_number * sublevels * loop


def _wanted_create(files_number, dirs_number, sublevels, loop):
    """
    Helper function to compute the wanted number of create events
    """
    # hack to prevent ugly if/else branching mess
    dirs_number_p = dirs_number
    sublevels_p = sublevels
    if sublevels == 0:
        sublevels = 1
    if dirs_number == 0:
        dirs_number = 1
    if loop == 0:
        loop = 1

    if dirs_number_p != 0 and sublevels_p != 0:
        return ((files_number * dirs_number * sublevels ) + sublevels * (1 + dirs_number_p)) * loop
    else:
        return ((files_number * dirs_number * sublevels ) + dirs_number_p + sublevels_p) * loop


class TestTreeWatcher(unittest.TestCase):
    """
    Our test class.
    We watch a specified directory, create some particular tree structure in it
    and check if we've got the rigght number of inotify events
    """

    def setup_helper(self, callbacks, workers=1):
        """
        Helper that set the state of the treewatcher.
        It avoids a lot of copy and paste between test files
        """
        self.test_dir = tempfile.mkdtemp()
        self.stm = choose_source_tree_monitor()
        self.callbacks = callbacks
        self.stm.set_events_callbacks(self.callbacks)
        self.stm.set_workers_number(workers)
        self.stm.start()
        self.stm.add_source_dir(self.test_dir)


    def setUp(self):
        """
        This function is called before each test
        We create and start our tree watcher

        It should be overriden in children.
        """
        self.setup_helper(callbacks=EventsCallbacks())


    def tearDown(self):
        """
        This function is called after each test
        We perform some cleaning
        """
        self.stm.stop()
        shutil.rmtree(self.test_dir)


    def _check_count_bool(self, files_number, dirs_number=0, sublevels=0, loop_iter=1):
        """
        Helper function to check if we've got the right number of events, returns a boolean
        """
        return self.callbacks.get_create_counter() == _wanted_create(files_number, dirs_number, sublevels, loop_iter) and \
               self.callbacks.get_cw_counter() == _wanted_close_write(files_number, dirs_number, sublevels, loop_iter)


    def _check_count(self, files_number, dirs_number=0, sublevels=0, loop_iter=1):
        """
        Helper function to check if we've got the right number of events, using assertEqual
        """
        ce_got = self.callbacks.get_create_counter()
        ce_wanted = _wanted_create(files_number, dirs_number, sublevels, loop_iter)
        cw_got = self.callbacks.get_cw_counter()
        cw_wanted = _wanted_close_write(files_number, dirs_number, sublevels, loop_iter)
        self.assertEqual(ce_got, ce_wanted, '''Got %d 'create events' instead of %d.''' % (ce_got, ce_wanted))
        self.assertEqual(cw_got, cw_wanted, '''Got %d 'close_write' events instead of %d.''' % (cw_got, cw_wanted))


    def _run_helper(self, files_number, dirs_number=0, sublevels=0, timeout=1, loop_iter=1):
        """
        Helper function to create a specific tree and checks for events
        """
        until_predicate = lambda: self._check_count_bool(files_number, dirs_number, sublevels=sublevels, loop_iter=loop_iter)
        create_files_tree(self.test_dir, files_number=files_number, dirs_number=dirs_number, sublevels=sublevels)
        self.stm.process_events(timeout=timeout, until_predicate=until_predicate)


    def _test_helper(self, files_number=0, dirs_number=0, loop=1, timeout=1, sublevels=0, cleanup=False):
        """
        Helper function that run tests
        It will create the files tree using parameters (see create_files),
        eventually in a loop (to stress inotify events handling) and check
        if we've got what we want.
        """
        for i in xrange(loop):
            self._run_helper(files_number, dirs_number, sublevels=sublevels, timeout=timeout, loop_iter=i+1)
            if cleanup:
                clean_dir(self.test_dir)
        self._check_count(files_number=files_number, dirs_number=dirs_number, sublevels=sublevels, loop_iter=loop)


    def test_nosublevel_onefile(self):
        """
        Test: one file in our watched dir
        """
        self._test_helper(files_number=1)


    def test_nosublevel_onefile_loop(self):
        """
        Test: one file in our watched dir, in a loop
        """
        self._test_helper(files_number=1, loop=10)


    def test_nosublevel_onedir(self):
        """
        Test: one dir in our watched dir
        """
        self._test_helper(dirs_number=1)


    def test_nosublevel_onedir_loop(self):
        """
        Test: one dir in our watched dir, in a loop
        """
        self._test_helper(dirs_number=1, loop=10)


    def test_nosublevel_manyfiles(self):
        """
        Test: many file in our watched dir
        """
        self._test_helper(files_number=999)


    def test_nosublevel_manyfiles_loop(self):
        """
        Test: many file in our watched dir, in a loop
        """
        self._test_helper(files_number=999, loop=10)


    def test_nosublevel_manydirs(self):
        """
        Test: many dirs in our watched dir
        """
        self._test_helper(dirs_number=999)


    def test_nosublevel_manydirs_loop(self):
        """
        Test: many dirs in our watched dir, in a loop
        """
        self._test_helper(dirs_number=999, loop=10, cleanup=True)


    def test_nosublevel_manydirs_and_files(self):
        """
        Test: many dirs and files in our watched dir
        """
        self._test_helper(files_number=10, dirs_number=999)


    def test_nosublevel_manydirs_and_files_loop(self):
        """
        Test: many dirs and files in our watched dir, in a loop
        """
        self._test_helper(files_number=10, dirs_number=999, loop=10, cleanup=True)


    def test_one_sublevel_one(self):
        """
        Test: one file in a subdir in our watched dir
        """
        self._test_helper(files_number=1, dirs_number=0, sublevels=1, loop=1)


    def test_one_sublevel_one_loop(self):
        """
        Test: one file in a subdir in our watched dir, in a loop
        """
        self._test_helper(files_number=1, dirs_number=0, sublevels=1, loop=10)


    def test_one_sublevel_many(self):
        """
        Test: many files in a subdir in our watched dir
        """
        self._test_helper(files_number=999, dirs_number=0, sublevels=1, loop=1)


    def test_one_sublevel_many_loop(self):
        """
        Test: many files in a subdir in our watched dir, in a loop
        """
        self._test_helper(files_number=999, dirs_number=0, sublevels=1, loop=10)


    def test_one_sublevel_many_dirs(self):
        """
        Test: many dirs in a subdir in our watched dir
        """
        self._test_helper(dirs_number=999, sublevels=1, loop=1)


    def test_one_sublevel_many_dirs_loop(self):
        """
        Test: many files in a subdir in our watched dir, in a loop
        """
        self._test_helper(dirs_number=999, sublevels=1, loop=10, cleanup=True)


    def test_one_sublevel_many_files_and_dir(self):
        """
        Test: many dirs and files in a subdir in our watched dir
        """
        self._test_helper(files_number=10, dirs_number=999, sublevels=1, loop=1)


    def test_one_sublevel_many_files_and_dirs_loop(self):
        """
        Test: many files and files in a subdir in our watched dir, in a loop
        """
        self._test_helper(files_number=10, dirs_number=999, sublevels=1, loop=10, cleanup=True)


    def test_many_sublevels_many_files_and_dir(self):
        """
        Test: many dirs and files in many subdir in our watched dir
        """
        self._test_helper(files_number=10, dirs_number=99, sublevels=7, loop=1)


    def test_many_sublevels_many_files_and_dirs_loop(self):
        """
        Test: many files and files in a subdir in our watched dir, in a loop
        """
        self._test_helper(files_number=10, dirs_number=99, sublevels=7, loop=10)

