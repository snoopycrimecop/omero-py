#!/usr/bin/env python
#
# Copyright 2009 Glencoe Software, Inc.  All Rights Reserved.
# Use is subject to license terms supplied in LICENSE.txt
#
"""
OMERO Support for temporary files and directories
"""

import os
import sys
import atexit
import logging
import tempfile
import threading
import traceback
import exceptions
import portalocker

from path import path

# TODO:
#  - locking for command-line cleanup
#  - plugin for cleaning unlocked files
#  - plugin for counting sizes, etc.
#  - decorator

class TempFileManager(object):
    """
    Creates temporary files and folders and makes a best effort
    to remove them on exit (or sooner). Typically only a single
    instance of this class will exist ("manager" variable in this
    module below)
    """

    def __init__(self, prefix = "omero"):
        """
        Initializes a TempFileManager instance with a userDir containing
        the given prefix value, or "omero" by default. Also registers
        an atexit callback to call self.cleanup() on exit.
        """
        self.logger = logging.getLogger("omero.util.TempFileManager")
        self.is_win32 = ( sys.platform == "win32" )
        self.prefix = prefix

        self.userdir = self.tmpdir() / ("%s_%s" % (self.prefix, self.username()))
        """
        User-accessible directory of the form $TMPDIR/omero_$USERNAME.
        If the given directory is not writable, an attempt is made
        to use an alternative
        """
        if not self.create(self.userdir) and not self.access(self.userdir):
            i = 0
            while i < 10:
                t = path("%s_%s" % (self.userdir, i))
                if self.create(t) or self.access(t):
                    self.userdir = t
                    break
            raise exceptions.Exception("Failed to create temporary directory: %s" % self.userdir)
        self.dir = self.userdir / self.pid()
        """
        Directory under which all temporary files and folders will be created.
        An attempt to remove a path not in this directory will lead to an
        exception.
        """
        if not self.dir.exists():
            self.dir.makedirs()
        self.lock = open(str(self.dir / ".lock"), "a+")
        """
        .lock file under self.dir which is used to prevent other
        TempFileManager instances (also in other languages) from
        cleaning up this directory.
        """
        try:
            portalocker.lock(self.lock, portalocker.LOCK_EX|portalocker.LOCK_NB)
        except:
            self.lock.close()
            raise
        atexit.register(self.cleanup)

    def cleanup(self):
        """
        Deletes self.dir and releases self.lock
        """
        self.clean_tempdir()
        self.lock.close() # Allow others access

    def tmpdir(self):
        """
        Returns a platform-specific user-writable temporary directory
        """
        return path(tempfile.gettempdir())

    def username(self):
        """
        Returns the current OS-user's name
        """
        if self.is_win32:
            import win32api
            return win32api.GetUserName()
        else:
            return os.getlogin()

    def pid(self):
        """
        Returns some representation of the current process's id
        """
        return str(os.getpid())

    def access(self, dir):
        """
        Returns True if the current user can write to the given directory
        """
        dir = str(dir)
        return os.access(dir, os.W_OK)

    def create(self, dir):
        """
        If the given directory doesn't exist, creates it (with mode 0700) and returns True.
        Otherwise False.
        """
        dir = path(dir)
        if not dir.exists():
            dir.makedirs(0700)
            return True
        return False

    def gettempdir(self):
        """
        Returns the directory under which all temporary
        files and folders will be created.
        """
        return self.dir

    def create_path(self, prefix, suffix, folder = False, text = False, mode = "r+"):
        """
        Uses tempfile.mkdtemp and tempfile.mkstemp to create temporary
        folders and files, respectively, under self.dir
        """

        if folder:
            name = tempfile.mkdtemp(prefix = prefix, suffix = suffix, dir = self.dir)
            self.logger.debug("Added folder %s", name)
        else:
            fd, name = tempfile.mkstemp(prefix = prefix, suffix = suffix, dir = self.dir, text = text)
            self.logger.debug("Added file %s", name)
            try:
                os.close(fd)
            except:
                self.logger.warn("Failed to close fd %s" % fd)

        return path(name)

    def remove_path(self, name):
        """
        If the given path is under self.dir, then it is deleted
        whether file or folder. Otherwise, an exception is thrown.
        """
        p = path(name)
        parpath = p.parpath(self.dir)
        if len(parpath) < 1:
            raise exceptions.Exception("%s is not in %s" % (p, self.dir))

        if p.exists():
            if p.isdir():
                p.rmtree(onerror = self.on_rmtree)
                self.logger.debug("Removed folder %s", name)
            else:
                p.remove()
                self.logger.debug("Removed file %s", name)

    def clean_tempdir(self):
        """
        Deletes self.dir
        """
        dir = self.gettempdir()
        self.logger.debug("Removing tree: %s", dir)
        dir.rmtree(onerror = self.on_rmtree)

    def clean_userdir(self):
        """
        Attempts to delete all directories under self.userdir
        other than the one owned by this process. If a directory
        is locked, it is skipped.
        """
        self.logger.debug("Cleaning user dir: %s" % self.userdir)
        dirs = self.userdir.dirs()
        for dir in dirs:
            if str(dir) == str(self.dir):
                self.logger.debug("Skipping self: %s", dir)
                continue
            lock = dir / ".lock"
            f = open(str(lock),"r")
            try:
                portalocker.lock(f, portalocker.LOCK_EX|portalocker.LOCK_NB)
            except:
                print "Locked: %s" % dir
                continue
            dir.rmtree(self.on_rmtree)
            print "Deleted: %s" % dir

    def on_rmtree(self, func, name, exc):
        self.logger.error("rmtree error: %s('%s') => %s", func.__name__, name, exc[1])

manager = TempFileManager()
"""
Global TempFileManager instance for use by the current process and
registered with the atexit module for cleaning up all created files on exit.
Other instances can be created for specialized purposes.
"""

def create_path(prefix = "omero", suffix = ".tmp", folder = False):
    """
    Uses the global TempFileManager to create a temporary file.
    """
    return manager.create_path(prefix, suffix, folder = folder)

def remove_path(file):
    """
    Removes the file from the global TempFileManager. The file will be deleted
    if it still exists.
    """
    return manager.remove_path(file)

def gettempdir():
    """
    Returns the dir value for the global TempFileManager.
    """
    return manager.gettempdir()

if __name__ == "__main__":

    from omero.util import configure_logging

    if len(sys.argv) > 1:
        args = sys.argv[1:]

        if "--debug" in args:
            configure_logging(loglevel=logging.DEBUG)
        else:
            configure_logging()

        if "clean" in args:
            manager.clean_userdir()
            sys.exit(0)
        elif "dir" in args:
            print manager.gettempdir()
            sys.exit(0)
        elif "lock" in args:
            print "Locking %s" % manager.gettempdir()
            raw_input("Waiting on user input...")
            sys.exit(0)

    print "Usage: %s clean" % sys.argv[0]
    print "   or: %s dir  " % sys.argv[0]
    sys.exit(2)
