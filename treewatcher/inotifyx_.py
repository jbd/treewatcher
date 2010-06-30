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
inotifyx based tree monitor
"""

import os
import errno
import inotifyx
import time
import sys
import threading
import multiprocessing
import logging

import Queue

from treewatcher import SourceTreeMonitor

_INOTIFYX_STM_LOGGER = logging.getLogger('_INOTIFYX_STM_LOGGER')
_INOTIFYX_STM_LOGGER.setLevel(logging.INFO)
_INOTIFYX_STM_LOGGER.addHandler(logging.StreamHandler())

class InotifyxSourceTreeMonitor(SourceTreeMonitor):
    """
    inotifyx based tree monitor class
    """

    def __init__(self):
        """
        Init. Nothing fancy here.
        """
        SourceTreeMonitor.__init__(self)
        self.inotifyx = inotifyx
        self.event_mask = (
          inotifyx.IN_DELETE |
          inotifyx.IN_CREATE |
          inotifyx.IN_CLOSE_WRITE |
          inotifyx.IN_MOVED_FROM |
          inotifyx.IN_MOVED_TO |
          inotifyx.IN_ATTRIB
        )

        self.wd_to_path = {}
        self.path_to_wd = {}
        self.inotify_fd = None


    def start(self, debug = False):
        """
        start inotifyx subsystem
        """
        self.inotify_fd = self.inotifyx.init()


    def _watch_dir(self, real_path):
        """
        Add an inotify watch on 'real_path'
        """
        if real_path in self.path_to_wd or not os.path.isdir(real_path):
            # already watching, or file
            return False

        watch_fd = self.inotifyx.add_watch(self.inotify_fd, real_path, self.event_mask)

        # FIXME: What happens if inotifyx has an error?
        if watch_fd > 0:
            # watch successful
            self.path_to_wd[real_path] = watch_fd
            self.wd_to_path[watch_fd] = real_path
            return True
        else:
            # watch unsuccessful, clean up
            self._rm_watch(watch_fd)
            return False


    def _unwatch_dir_helper(self, real_path):
        """
        Remove a watch on the specified path
        """
        try:
            watch_fd = self.path_to_wd[real_path]
        except KeyError:
            # not watching
            return

        self._rm_watch(watch_fd)
        del self.path_to_wd[real_path]
        del self.wd_to_path[watch_fd]


    def _unwatch_dir(self, real_path):
        """
        Remove a watch on the specified path and all
        its children
        """
        # we cannot use iterkeys here, because the dictionnary
        # is likely to change during iteration
        for path in self.path_to_wd.keys():
            if path.startswith(real_path):
                self._unwatch_dir_helper(path)


    def _rm_watch(self, watch_fd):
        """
        Remove an inotify watch on the specified path
        """
        try:
            self.inotifyx.rm_watch(self.inotify_fd, watch_fd)
        except IOError, err:
            if err.errno != errno.EINVAL:
                raise

    ### SourceTreeMonitor API:

    def stop(self):
        """
        Stop inotifyx subsystem
        Call it from the same thread you've started your file monitor !
        """
        os.close(self.inotify_fd)


    def _add_source_dir(self, path, do_events=True):
        """
        Add a source_dir recursively
        """
        success = self._watch_dir(path)
        if not success:
            return
        try:
            names = os.listdir(path)
        except (OSError, IOError):
            return
        for name in names:
            sub_path = os.path.join(path, name)
            isdir = os.path.isdir(sub_path)
            if do_events:
                self.events_callbacks._create(sub_path, isdir)
            if not isdir and do_events:
                # if we detect a file, we assume its ready to read.
                # The not ready case has to handled in the callback.
                # If the file it's not ready, we assume that a normal
                # IN_CLOSE_WRITE event will we triggered by the inotify subsystem
                self.events_callbacks._close_write(sub_path, isdir)
            elif isdir:
                self._add_source_dir(sub_path, do_events=do_events)


    def add_source_dir(self, path):
        """
        Add a source_dir recursively
        """
        self._add_source_dir(path, do_events=False)


    def _remove_source_dir(self, real_path):
        """
        Remove watch from real_path
        """
        self._unwatch_dir(real_path)


    def remove_source_file(self, real_path):
        """
        Needed for API compliance
        """
        pass

    def _process_event(self, event):
        """
        Process one inotify event
        """
        try:
            basepath = self.wd_to_path[event.wd]
        except KeyError:
            # We got an event for a path that we are no longer watching.  If
            # the event is IN_IGNORED, this is expected since we get IN_IGNORED
            # when we remove the watch, which happens after the directory is
            # removed.  Otherwise, the event is late, which won't usually
            # happen for other event types, but could if paths were rapidly
            # added and removed.
            if not (event.mask & self.inotifyx.IN_IGNORED):
                logging.debug (
                  'InotifyxSourceTreeMonitor: late event: %s, %r' %
                  (event, event)
                )
            return

        if event.name:
            path = os.path.join(basepath, event.name)
        else:
            path = basepath

        is_dir = bool(event.mask & self.inotifyx.IN_ISDIR)
        events_cb = self.events_callbacks

        if event.mask & self.inotifyx.IN_CREATE:
            events_cb._create(path, is_dir)
            # we manually handle any created subdir
            if is_dir:
                self._add_source_dir(path)
        elif event.mask & self.inotifyx.IN_DELETE:
            events_cb._delete(path, is_dir)
            # we manually handle any deleted subdir
            if is_dir:
                self._remove_source_dir(path)
        elif event.mask & self.inotifyx.IN_CLOSE_WRITE:
            events_cb._close_write(path, is_dir)
        elif event.mask & self.inotifyx.IN_MOVED_FROM:
            events_cb._moved_from(path, is_dir)
            if is_dir:
                self._remove_source_dir(path)
        elif event.mask & self.inotifyx.IN_MOVED_TO:
            events_cb._moved_to(path, is_dir)
        elif event.mask & self.inotifyx.IN_MODIFY:
            events_cb._modify(path, is_dir)
        elif event.mask & self.inotifyx.IN_ATTRIB:
            events_cb._attrib(path, is_dir)
        elif event.mask & self.inotifyx.IN_UNMOUNT:
            events_cb._unmount(path, is_dir)
            if is_dir:
                self._remove_source_dir(path)
        elif event.mask & self.inotifyx.IN_IGNORED:
            pass
        elif event.mask & self.inotifyx.IN_Q_OVERFLOW:
            logging.debug(
              'InotifyxSourceTreeMonitor: '
              'event queue overflowed, events were probably lost'
            )
        else:
            raise ValueError(
              'failed to match event mask: %s' % event.get_mask_description()
            )


    def _get_events(self, block=False):
        """
        Retrieve events from inotify, without blocking by default
        See below.
        """
        if block:
            return self.inotifyx.get_events(self.inotify_fd)
        else:
            return self.inotifyx.get_events(self.inotify_fd, 0)


    def _process_events_internal(self, block=False):
        """
        Internal event process loop
        """
        for event in self._get_events(block=block):
            self._process_event(event)


    def _start_events_queue_processing(self, ev_queue=None):
        """
        This internal function encapsulate the logic around the events_queue
        depending on the type of the callback.

        This function is used in serial, threaded an multiprocessing mode.
        In the last two mode, this function is the target argument of the
        Thread/Process constructor
        """
        # TODO: the multiprocessing mode does not work like i want
        # when i've got shared state between callback. I need to figure
        # out why
        if self.events_callbacks._multiprocessing:
            events_queue = ev_queue
        else:
            events_queue = self.events_queue

        # some lambda logic function to have a "clean" while loop condition
        if not self.events_callbacks._serial:
            continue_condition = lambda: True
        else:
            # it's safe to call empty here because there is not concurrent access
            # to the events_queue
            continue_condition = lambda: not events_queue.empty()

        while continue_condition():
            event = events_queue.get()
            if event is None:
                events_queue.task_done()
                break
            # we retrieve a event triplet like ('create', '/tmp/foo', True)
            # we call the adequate function of the events_callbacks object
            callback = getattr(self.events_callbacks, event[0], None)
            if callback:
                callback(event[1], event[2])
            events_queue.task_done()

        # need to put None here to handle threads/processes join !
        if not self.events_callbacks._serial:
            events_queue.put(None)


    def _start_events_queue_processes(self, number):
        """
        This internal function handles the threads/processes creation
        in threaded and multiprocessing mode.

        It returns the list of the threads/processes created to join on them
        when the work is finished.
        """
        processes = []
        for _ in range(number):
            if self.events_callbacks._threaded:
                processes.append(threading.Thread(target=self._start_events_queue_processing))
            elif self.events_callbacks._multiprocessing:
                processes.append(multiprocessing.Process(target=self._start_events_queue_processing, args=(self.events_queue,)))
            else:
                assert False, "Cannot start processes or threads in serial mode."
            processes[-1].start()

        return processes


    def process_events(self, timeout=None, until_predicate=None, sleep_delay=0.1):
        """
        Event process loop during timeout seconds at most or when the predicate became true

        If the user specify an until_predicate callable, we don't block on getting inotify
        event. Instead, we retrieve events using non blocking mode and we sleep during sleep_delay
        before evaluating the predicate again.

        If the user didn't provide a timeout and a predicate function, we block on getting inotify
        events.
        """

        if not timeout:
            timeout = sys.maxint

        if not self.events_callbacks._serial:
            processes = self._start_events_queue_processes(number=self.workers)
        # we want to block if the user didn't specify any timeout and no until_predicate function
        block = False
        if timeout == sys.maxint and not until_predicate:
            block = True

        # hack to make the while loop work even if no predicate function is given
        if not until_predicate:
            until_predicate = lambda: False

        start = time.time()
        delay = 0

        try:
            while delay < timeout and not until_predicate():
                self._process_events_internal(block=block)
                if self.events_callbacks._serial:
                    self.events_queue.put(None)
                    self._start_events_queue_processing()
                if not block:
                    time.sleep(sleep_delay)
                delay = time.time() - start

        finally:
            # we tell the threads/processes to stop
            if not self.events_callbacks._serial:
                self.events_queue.put(None)
                map(lambda p: p.join(), processes)
            # we make replace the current queue by an empty one
            self.reset_queue()
