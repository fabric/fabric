"""
Module mimicking python os module. As pythonistas we should be comfortable
interacting with the underlaying operating system using the os module.

Inspired by Ali-Akber Saifee module rfsutil (https://github.com/alisaifee/fabric/blob/master/fabric/contrib/rfsutil.py). Difference is this module doesn't open another channel to perform the os interactions. The underlying fabric channels are used 
"""

from fabric.api import *


def stat(filename, use_sudo=False):
    """
    Return the stats for a file/directory

    Return format will be posix.stat_result 
    like the os.stat module
    """
    import posix

    func = use_sudo and sudo or run
    if exists(filename):
        with settings(hide('everything'), warn_only=True):
            output = func("stat '%s'" % filename)
    return output
