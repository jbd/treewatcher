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
Unit tests for the tree watcher library
"""

import os
import shutil
import unittest
import tempfile

from treewatcher import choose_source_tree_monitor
from treewatcher import EventsCallbacks


class TestsCallbacks(EventsCallbacks):
    """
    Callbacks class for testing purpose
    We will count events and check if we got 
    the right number
    """
    def __init__(self):
        EventsCallbacks.__init__(self)
        self.create_counter = 0
        self.cw_counter = 0
        self.create_dir = 0
        self.create_file = 0

    def create(self, path, is_dir):
        """ Impressive function """
        self.create_counter += 1
        if is_dir:
            self.create_dir += 1
        else:
            self.create_file += 1

    def close_write(self, path, is_dir):
        """ Again """
        self.cw_counter += 1


def create_files(where, number, dirs_number=0):
    """
    This function will create files in the 'where' directory. 
    It's behaviour depends on the value of the dirs_number parameter
    - if dirs_number is 0 (default), number designates the number of files
    which will be created in the where directory.
    - if dirs_number is not 0, dirs_number folders will be created with 'number' files
      in each of them
    """
    if dirs_number == 0:
        for i in range(number):
            myfile = tempfile.mkstemp(prefix=('%02d' % i + '_'), dir=where)
            os.close(myfile[0])
    else:
        for i in range(dirs_number):
            location = tempfile.mkdtemp(prefix=('%02d' % i + '_'), dir=where)
            for j in range(number):
                myfile = tempfile.mkstemp(prefix=('%02d' % j + '_'), dir=location)
                os.close(myfile[0])


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


def _wanted_close_write(files_number, dirs_number=0, loop=1):
    """
    Helper function to compute the wanted number of close_write events
    """
    if dirs_number != 0:
        return files_number * dirs_number * loop
    else:
        return files_number * loop


def _wanted_create(files_number, dirs_number=0, loop=1):
    """
    Helper function to compute the wanted number of create events
    """
    if dirs_number != 0:
        return (files_number * dirs_number + dirs_number) * loop
    else:
        return files_number * loop


class TestTreeWatcher(unittest.TestCase):
    """
    Our test class.
    We watch a specified directory, create some particular tree structure in it
    and check if we've got the rigght number of inotify events
    """
    def setUp(self):
        """
        This function is called before each test
        We create and start our tree watcher
        """
        self.test_dir = tempfile.mkdtemp()
        self.stm = choose_source_tree_monitor()
        self.callbacks = TestsCallbacks()
        self.stm.set_events_callbacks(self.callbacks)
        self.stm.start()
        self.stm.add_source_dir(self.test_dir)

    def tearDown(self):
        """
        This function is called after each test
        We perform some cleaning
        """
        self.stm.stop()
        shutil.rmtree(self.test_dir)


    def _check_count_bool(self, files_number, dirs_number=0, loop_iter=1):
        """
        Helper function to check if we've got the right number of events, returns a boolean
        """
        return self.callbacks.create_counter == _wanted_create(files_number, dirs_number, loop_iter) and \
               self.callbacks.cw_counter == _wanted_close_write(files_number, dirs_number, loop_iter)

    def _check_count(self, files_number, dirs_number=0, loop_iter=1):
        """
        Helper function to check if we've got the right number of events, using assertEqual
        """
        self.assertEqual(self.callbacks.create_counter, _wanted_create(files_number, dirs_number, loop_iter))
        self.assertEqual(self.callbacks.cw_counter, _wanted_close_write(files_number, dirs_number, loop_iter))

    def _run_helper(self, files_number, dirs_number=0, timeout=1, loop_iter=1):
        """
        Helper function to create a specific tree and checks for events
        """
        until_predicate = lambda: self._check_count_bool(files_number, dirs_number, loop_iter=loop_iter) 
        create_files(self.test_dir, files_number, dirs_number)
        self.stm.process_events_timeout(timeout=timeout, until_predicate=until_predicate)


    def _test_helper(self, files_number, dirs_number=0, loop=1, timeout=1, sublevels=0, cleanup=True):
        """
        Helper function that run tests
        It will create the files tree using parameters (see create_files),
        eventually in a loop (to stress inotify events handling) and check
        if we've got what we want.
        """
        for i in xrange(loop):
            self._run_helper(files_number, dirs_number, timeout=timeout, loop_iter=i+1)
            if cleanup:
                clean_dir(self.test_dir)
        self._check_count(files_number=files_number, dirs_number=dirs_number, loop_iter=loop)


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


    def test_one_sublevel_one(self):
        """ 
        Test: one file in a subdir in our watched dir
        """
        self._test_helper(files_number=1, dirs_number=1, loop=1)


    def test_one_sublevel_one_loop(self):
        """ 
        Test: one file in a subdir in our watched dir, in a loop
        """
        self._test_helper(files_number=1, dirs_number=1, loop=10)


    def test_one_sublevel_many(self):
        """ 
        Test: many files in a subdir in our watched dir
        """
        self._test_helper(files_number=999, dirs_number=10, loop=1)


    def test_one_sublevel_many_loop(self):
        """ 
        Test: many files in a subdir in our watched dir, in a loop
        """
        self._test_helper(files_number=999, dirs_number=10, loop=10)


def main():
    """
    Main function
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTreeWatcher)
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == "__main__":
    main()
