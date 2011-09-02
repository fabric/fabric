"""
module mimicking python os module. as pythonistas we should be comfortable
interacting with the underlaying operating system using the os module.

inspired by ali-akber saifee module rfsutil (https://github.com/alisaifee/fabric/blob/master/fabric/contrib/rfsutil.py). difference is this module doesn't open another channel to perform the os interactions. the underlying fabric channels are used 
"""
import datetime
import time
import mx.DateTime as mx

from fabric.api import *
from fabric.contrib.files import exists 

def is_datetime(value):
    return isinstance(value, (datetime.date, datetime.datetime, datetime.time))

def is_string(value):
    return isinstance(value, basestring)

def _convert_to_epoch(dt):
    """
    Convert python datetime to epoch
    """
    #http://www.testingreflections.com/node/view/5218
    #http://bugs.python.org/issue2736
    return time.mktime(dt.timetuple()) + (dt.microsecond / 1000000.0)

def convert_to_epoch(time_val):
    """
    Figure out what we are passed convert and
    then convert it to python datetime. Using 
    python datetime we can easily convert to 
    epoch.
    """
    if is_datetime(time_val):
        return _convert_to_epoch(time_val)

    if is_string(time_val):
        parser = mx.DateTimeFrom
        if '-' not in time_val:
            parser = mx.Parser.TimeFromString
        dt = parser(time_val, formats=['iso']).pydatetime()
        return _convert_to_epoch(dt)

def stat(filename, use_sudo=False):
    """
    Return the stats for a file/directory

    Return format will be posix.stat_result 
    like the os.stat module
    """
    import re
    import posix

    func = use_sudo and sudo or run
    if exists(filename):
        with settings(hide('everything'), warn_only=True):
            output = func("stat '%s'" % filename)

        size = re.search('Size:[ 0-9]+',output).group(0).split(':')[1].strip()
        blocks = re.search('Blocks:[ 0-9]+',output).group(0).split(':')[1].strip()
        block = re.search('IO Block:[ 0-9]+',output).group(0).split(':')[1].strip()
        inode = re.search('Inode:[ 0-9]+',output).group(0).split(':')[1].strip()
        nlink = re.search('Links:[ 0-9]+',output).group(0).split(':')[1].strip()

        device_part = re.search('Device:[ /0-9a-zA-Z]+',output).group(0).split(':')[1].strip()
        device =  re.search('[0-9]+',device_part.split('/')[1].strip()).group(0)

        uid_part = re.search('Uid:[ \(\)\\0-9a-zA-Z]+',output).group(0).split(':')[1].strip()
        uid = re.search('[0-9]+',uid_part).group(0).strip()

        gid_part = re.search('Gid:[ \(\)\\0-9a-zA-Z]+',output).group(0).split(':')[1].strip()
        gid = re.search('[0-9]+',gid_part).group(0).strip()

        access_rows = re.findall('Access:.+\r\n',output)
        mode_part = re.search('Access:[ \(\)/\-rwx0-9]+',access_rows[0])
        mode = re.search('[0-9]+',mode_part.group(0)).group(0).strip()

        access = re.search('Access:.+\r\n',access_rows[1]).group(0)[7:].strip()
        atime = convert_to_epoch(access)

        modify = re.search('Modify:.+\r\n',output).group(0)[7:].strip()
        mtime = convert_to_epoch(modify)

        change = re.search('Change:.+',output).group(0)[7:].strip()
        ctime = convert_to_epoch(change)

        #print output
        return posix.stat_result((mode, inode, device, nlink, uid, gid, block, atime, mtime, ctime))
    return None

def listdir(path='', use_sudo=False):
    """
    Return a list containing the names of the entries in the directory given by path. 
    The list is in arbitrary order. It does not include the special entries '.' and '..' even if they are present in the directory.
    """

    items_at_path = []

    func = use_sudo and sudo or run
    output = func("ls %s" % path)
    items_at_path = output.split()
    
    return items_at_path

def remove(path, use_sudo=False):
    """
    Remove (delete) the file path. If path is a directory, OSError is raised; see rmdir() below to remove a directory. 
    This is identical to the unlink() function documented below. On Windows, attempting to remove a file that is in use causes an exception to be raised; 
    on Unix, the directory entry is removed but the storage allocated to the file is not made available until the original file is no longer in use.
    """

    func = use_sudo and sudo or run
