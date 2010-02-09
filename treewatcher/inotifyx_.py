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

from treewatcher import SourceTreeMonitor

class InotifyxSourceTreeMonitor(SourceTreeMonitor):
    """
    inotifyx based tree monitor class
    """
    wd_to_path = None
    path_to_wd = None
    fd = None

    def __init__(self):
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


    def _unwatch_dir(self, real_path):
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
        """
        os.close(self.inotify_fd)


    def add_source_dir(self, path):
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
            self.events_callbacks.create(sub_path, isdir)
            if not isdir:
                self.events_callbacks.close_write(sub_path, isdir)


    def remove_source_dir(self, real_path):
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
                print (
                  'InotifyxSourceTreeMonitor: late event: %s, %r',
                  event,
                  event,
                )
            return

        if event.name:
            path = os.path.join(basepath, event.name)
        else:
            path = basepath

        is_dir = bool(event.mask & self.inotifyx.IN_ISDIR)
        events_cb = self.events_callbacks

        if event.mask & self.inotifyx.IN_CREATE:
            events_cb.create(path, is_dir)
            if is_dir:
                self.add_source_dir(path)
        elif event.mask & self.inotifyx.IN_DELETE:
            events_cb.delete(path, is_dir)
        elif event.mask & self.inotifyx.IN_CLOSE_WRITE:
            events_cb.close_write(path, is_dir)
        elif event.mask & self.inotifyx.IN_MOVED_FROM:
            events_cb.moved_from(path, is_dir)
        elif event.mask & self.inotifyx.IN_MOVED_TO:
            events_cb.moved_to(path, is_dir)
        elif event.mask & self.inotifyx.IN_MODIFY:
            events_cb.update(path, is_dir)
        elif event.mask & self.inotifyx.IN_ATTRIB:
            events_cb.update(path, is_dir)
        elif event.mask & self.inotifyx.IN_UNMOUNT:
            events_cb.delete(path, is_dir)
        elif event.mask & self.inotifyx.IN_IGNORED:
            pass
        elif event.mask & self.inotifyx.IN_Q_OVERFLOW:
            print(
              'InotifyxSourceTreeMonitor: '
              'event queue overflowed, events were probably lost'
            )
        else:
            raise ValueError(
              'failed to match event mask: %s' % event.get_mask_description()
            )


    def _get_events(self):
        """
        Retrieve events from inotify, without blocking
        See below.
        """
        return self.inotifyx.get_events(self.inotify_fd, 0)

    def process_events(self):
        """
        Event process loop
        """
        for event in self._get_events():
            self._process_event(event)

    def process_events_timeout(self, timeout, until_predicate = None, sleep_delay = 0.1):
        """
        Event process loop during timeout seconds at most or when the predicate became true
        We use a sleep here instead of self.inotifyx.get_events(self.inotify_fd) (without a
        timeout parameter) to catch events early.
        """
        if not until_predicate:
            until_predicate = lambda: False
        start = time.time()
        delay = 0
        while delay < timeout and not until_predicate():
        #while delay < timeout:
            self.process_events()
            time.sleep(sleep_delay)
            delay = time.time() - start

