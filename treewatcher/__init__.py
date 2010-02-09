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
This file contains helpers function and interfaces classes SourceTreeMonitor and
EventsCallbacks
"""

import sys

SOURCE_TREE_MONITORS = (
  'treewatcher.inotifyx_.InotifyxSourceTreeMonitor',
)

class MissingDependency(Exception):
    """
    Give an explicit exception name in the context 
    of this file
    """
    pass


def _import_name(name):
    """
    Imports a Python module referred to by name, and returns that module.
    Raises an ImportError if the import fails.
    """
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        try:
            mod = getattr(mod, comp)
        except AttributeError:
            raise ImportError, '%s has no attribute %s' % (mod, comp)
    return mod


def _get_obj_by_dotted_name(dotted_name):
    """
    Helper function to deal with crappy things
    """
    # Note: both arguments to rpartition must be of same type (unicode, str).
    modname, _, objname = dotted_name.rpartition(type(dotted_name)('.'))
    mod = _import_name(modname)
    return getattr(mod, objname)


def _get_source_tree_monitor(dotted_name):
    """
    Helper function to deal with crappy things
    """
    source_tree_mon_cls = _get_obj_by_dotted_name(dotted_name)
    return source_tree_mon_cls()


def choose_source_tree_monitor(stm_dotted_name = None):
    """
    Convenience function to retrieve a given source tree monitor,
    or a specific one by given its dotted name. (ie: trewatcher.MyFileMonitor)
    """
    if stm_dotted_name is not None:
        candidates = [stm_dotted_name]
    else:
        candidates = SOURCE_TREE_MONITORS

    for candidate in candidates:
        try:
            stm = _get_source_tree_monitor(candidate)
        except MissingDependency, err:
            print >> sys.stderr, (
              'source tree monitor %s unsupported '
              'due to missing dependency %s'
            ) % (candidate, str(err))
        else:
            print >> sys.stderr, 'using source tree monitor %s' % candidate
            return stm

    raise AssertionError('unable to find a usable source tree monitor')


class EventsCallbacks(object):
    """
    Base class for defining callbacks
    """
    def __init__(self):
        self.source_tree_monitor = None

    def create(self, path, is_dir):
        """ callback called on a 'IN_CREATE' event """

    def delete(self, path, is_dir):
        """ callback called on a 'IN_DELETE' event """
    
    def close_write(self, path, is_dir):
        """ callback called on a 'IN_CLOSE_WRITE' event """

    def moved_from(self, path, is_dir):
        """ callback called on a 'IN_MOVED_FROM' event """

    def moved_to(self, path, is_dir):
        """ callback called on a 'IN_MOVED_TO' event """

    def modify(self, path, is_dir):
        """ callback called on a 'IN_MODIFY' event """

    def attrib(self, path, is_dir):
        """ callback called on a 'IN_ATTRIB' event """

    def unmount(self, path, is_dir):
        """ callback called on a 'IN_UNMOUNT' event """


class SourceTreeMonitor(object):
    """
    Source tree monitors need to implement this interface
    """
    events_callbacks = EventsCallbacks()

    def __init__(self):
        """Initialize."""

    def set_events_callbacks(self, events_obj):
        """ set the callbacks object for this monitor (see class EventsCallbacks) """
        self.events_callbacks = events_obj

    def start(self, debug = False):
        """Start monitoring the source tree."""

    def stop(self):
        """Stop monitoring the source tree; clean up."""

    def process_events(self):
        """Process pending events.  Do not block."""
    
    def process_events_timeout(self, timeout):
        """Process pending events.  Timeout block."""

    def add_source_dir(self, real_path):
        """
        Monitor source directory ``real_path``.  Fail silently if:

         * path does not exist
         * path exists but is not a directory
         * path exists but cannot be monitored (perhaps due to permissions)
         * path is already being watched
        """

    def remove_source_dir(self, real_path):
        """
        Stop monitoring source directory ``real_path``.  Fail silently if
        directory was not previously being monitored.
        """

