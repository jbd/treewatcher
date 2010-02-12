#!/usr/bin/env python
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
This script will run every tests file present in the same directory.
It uses helper.test_runner which takes a list a files.
See helper.test_runner for more information.
"""

import os
import glob
import helper


def main():
    """ Main function """
    current_dir = os.getcwd()
    testdir = os.path.dirname(__file__)
    os.chdir(testdir)
    try:
        test_files = [ f for f in glob.glob("test_*.py") if os.path.isfile(f) ]
        helper.tests_runner(test_files)
    finally:
        os.chdir(current_dir)


if __name__ == "__main__":
    main()
