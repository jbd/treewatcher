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

import os
import sys
import logging
import threading
import multiprocessing
import Queue


_SOURCETREEMON_LOGGER = logging.getLogger('_SOURCETREEMON_LOGGER')
_SOURCETREEMON_LOGGER.setLevel(logging.INFO)
_SOURCETREEMON_LOGGER.addHandler(logging.StreamHandler())


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
    or a specific one by given its dotted name. (ie: treewatcher.MyFileMonitor)
    """
    if stm_dotted_name is not None:
        candidates = [stm_dotted_name]
    else:
        candidates = SOURCE_TREE_MONITORS

    for candidate in candidates:
        try:
            stm = _get_source_tree_monitor(candidate)
        except MissingDependency, err:
            _SOURCETREEMON_LOGGER.error(
              'source tree monitor %s unsupported '
              'due to missing dependency %s'
              % (candidate, str(err)))
        else:
            _SOURCETREEMON_LOGGER.debug('using source tree monitor %s' % candidate)
            return stm

    raise AssertionError('unable to find a usable source tree monitor')


class _EventsCallbacks(object):
    """
    Internal base class for defining events callback.

    The implementation is quite tricky, but quite pretty i think.

    The main idea is that the tree monitor will internally call _create, _close_write, etc..
    (underscore + event name) and that we use some __getattribute__ magic to put the event is
    the events queue.
    """

    def __init__(self, _serial=True, _threaded=False, _multiprocesses=False):
        """
        This is an internal class with dirty hacks.
        """
        self._stm = None
        # _valid_events_internal needs to be defined here because of the test
        # in __getattribute__
        self._valid_events_internal = []
        self._valid_events = [ 'create', \
                              'delete', \
                              'close_write', \
                              'moved_from', \
                              'moved_to', \
                              'modify', \
                              'attrib', \
                              'unmount' ]
        self._valid_events_internal = [ '_' + value for value in self._valid_events ]
        self._serial = _serial
        self._threaded = _threaded
        self._multiprocessing = _multiprocesses

        assert (int(self._serial) + int(self._threaded) + int(self._multiprocessing)) == 1, \
                "A events callbacks object must be serial OR threaded OR multiprocessing"


    def __getattribute__(self, attr):
        """
        __getattribute__ with some lambda : dirty and magic.
        """
        if attr in object.__getattribute__(self, '_valid_events_internal'):
            # we return a lambda which is bind to a function that will put a triplet (event, path, is_dir)
            # on the event queue. We removed the first char '_' of attr to match the actual name in the 
            # child class
            return lambda path, is_dir: object.__getattribute__(self, '_stm').events_queue.put((attr[1:], path, is_dir))
        else:
            return object.__getattribute__(self, attr)


class EventsCallbacks(_EventsCallbacks):
    """
    Easy to use : inherit from it and implement a create, delete, close_write... function
    (see valid_events for a complete list), that's all.

    This class is for events that will be treated in the same process as the monitor
    """
    def __init__(self):
        """ init """
        _EventsCallbacks.__init__(self)



class ThreadedEventsCallbacks(_EventsCallbacks):
    """
    Just like EventsCallbacks, but since each function can be eventually called
    from different threads, you have to protect the shared state, if you've got one.
    """
    def __init__(self):
        """ init """
        _EventsCallbacks.__init__(self, _serial=False, _threaded=True)


class MultiProcessingEventsCallbacks(_EventsCallbacks):
    """
    !!! DOES NOT WORK the way i want. DO NOT USE !!!
    Just like EventsCallbacks, but since each function can be eventually called
    from different processes, you have to protect the shared state, if you've got one.
    """
    def __init__(self):
        """ init """
        _EventsCallbacks.__init__(self, _serial=False, _multiprocesses=True)


class SourceTreeMonitor(object):
    """
    Source tree monitors need to implement this interface
    """

    def __init__(self):
        """Initialize."""
        # this has to be set using set_events_callbacks
        self.events_callbacks = None
        # the events queue type depends on the type of self.events_callbacks
        self.events_queue = None
        # represents the number of threads/processes that will be use
        # to handle the callbacks
        self.workers = 1


    def reset_queue(self):
        """
        Helper function to reset the queue depending on the
        callbacks type (serial, threaded, etc ...)
        """
        if self.events_callbacks._multiprocessing:
            self.events_queue = multiprocessing.JoinableQueue()
        else:
            self.events_queue = Queue.Queue()


    def set_events_callbacks(self, events_obj):
        """ set the callbacks object for this monitor (see class EventsCallbacks) """
        self.events_callbacks = events_obj
        self.events_callbacks._stm = self
        self.reset_queue()


    def set_workers_number(self, workers):
        """
        Set the number of threads/processes that will be use to handle
        the callbacks
        """
        self.workers = workers


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

