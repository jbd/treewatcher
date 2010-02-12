#-*- coding: utf-8 -*-
#
# Copyright (c) 2010 Jean-Baptiste Denis.
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 or later as published by the Free
# Software Foundation.
#
# A copy of the license has been included in the COPYING file.

"""
This module implements some higher order functions based on unittest 
to deal with tests on the filesystem.
"""

import os
import unittest
from optparse import OptionParser


def tests_runner(files, run_suite=True):
    """
    This function takes a file or a list of files and run tests found in it/them.
    It will look inside each file for 'TESTS_TO_RUN' attribute to determine the tests
    to run. If 'run_suite' is set to True, the tests are launch. If it's False,
    a unittest.TestSuite is returned.

    This function is also (mmmm, bad design ? :D My goal was to write the less code possible
    in the test file...) used to parse the command line. If the '-l' is provided on the command
    line, all available test will be print on the standard output. If the user provides valids
    test name on the command line, only those tests will be run.

    Examples:
    =========

    $ ./run_all.py -l
    $ ./run_all.py TestEightThreadTreeWatcher.test_one_sublevel_one
    $ ./run_all.py TestEightThreadTreeWatcher
    $ ./run_all.py TestEightThreadTreeWatcher
    $ ./run_all.py TestEightThreadTreeWatcher.test_nosublevel_onefile TestTwoThreadTreeWatcher.test_nosublevel_onedir
    ...
    """

    # if the user provide a single file, we build a list on it
    if type(files) not in (list, tuple):
        files = [files]

    parser = OptionParser()
    parser.add_option('-l', '--list', dest="listtests", action="store_true", help="show available tests")
    (options, args) = parser.parse_args()

    # we override the function argument in case of a listing request
    if options.listtests:
        run_suite = False

    # to_run will hold the tests we want to run
    to_run = unittest.TestSuite()

    for current_file in files:
        # check for the 'TESTS_TO_RUN' attribute in each file
        current_file, _ = os.path.splitext(current_file)
        current_module = __import__(current_file)
        tests_to_run = getattr(current_module, 'TESTS_TO_RUN', None)
        if not tests_to_run or len(tests_to_run) == 0:
            continue
        # we build the test names manually. Maybe is there a better way ?
        tests_to_run = [ current_file + '.' + str(test) for test in tests_to_run ]
        tests_to_run_suite = unittest.TestLoader().loadTestsFromNames(tests_to_run)

        if options.listtests:
            for suite in tests_to_run_suite:
                # i'm not very happy here. I have to use the private variable _tests.
                # i didn't find a way to do without it. I should investigate more.
                for test in suite._tests:
                    print test.id().lstrip(current_file + '.')
            continue

        # the user didn't provide specific tests on the command line
        if len(args) == 0:
            # we run all the tests from tests_to_run
            to_run.addTests(tests_to_run_suite)

    # the user has provides specific tests on the command line
    if len(args) > 0:
        for current_file in files:
            cmdline_tests = [os.path.splitext(current_file)[0] + '.' + t for t in args]
            for test in cmdline_tests:
                try:
                    to_run.addTest(unittest.TestLoader().loadTestsFromName(test))
                except AttributeError:
                    pass

    if run_suite:
        unittest.TextTestRunner(verbosity=2).run(to_run)
    else:
        return to_run


