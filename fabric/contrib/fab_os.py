"""
module mimicking python os module. as pythonistas we should be comfortable
interacting with the underlaying operating system using the os module.

inspired by ali-akber saifee module rfsutil (https://github.com/alisaifee/fabric/blob/master/fabric/contrib/rfsutil.py). difference is this module doesn't open another channel to perform the os interactions. the underlying fabric channels are used 
"""
import datetime
import time

from fabric.api import *
from fabric.contrib.files import exists 

class Cannot(Exception):
    def __init__(self,change,to_change):
        self.change = change
        self.to_change = to_change

    def __str__(self):
        return 'Cannot %s `%s`: No such file or directory' % (self.change,self.to_change)

def stat(filename, use_sudo=False):
    """
    Return the stats for a file/directory

    Return format will be posix.stat_result 
    like the os.stat module
    """
    import posix

    func = sudo if use_sudo else run
    if exists(filename):
        with settings(hide('everything'), warn_only=True):
            output = func("stat -c '%%a %%i %%d %%h %%u %%g %%o %%X %%Y  %%Z' '%s'" % filename)
            return posix.stat_result(tuple(output.split()))
    raise Cannot('stat',filename)

def listdir(path='', use_sudo=False):
    """
    Return a list containing the names of the entries in the directory given by path. 
    The list is in arbitrary order. It does not include the special entries '.' and '..' even if they are present in the directory.
    """

    items_at_path = []

    func = sudo if use_sudo else run
    output = func("ls %s" % path)
    items_at_path = output.split()
    
    return items_at_path

def remove(path, use_sudo=False):
    """
    Remove (delete) the file path. If path is a directory, OSError is raised; see rmdir() below to remove a directory. 
    This is identical to the unlink() function documented below. On Windows, attempting to remove a file that is in use causes an exception to be raised; 
    on Unix, the directory entry is removed but the storage allocated to the file is not made available until the original file is no longer in use.
    """

    func = sudo if use_sudo else run
