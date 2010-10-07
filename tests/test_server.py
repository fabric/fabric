"""
Tests for the test server itself.

Not intended to be run by the greater test suite, only by specifically
targeting it on the command-line. Rationale: not really testing Fabric itself,
no need to pollute Fab's own test suite. (Yes, if these tests fail, it's likely
that the Fabric tests using the test server may also have issues, but still.)
"""
__test__ = False

from nose.tools import eq_, ok_
import paramiko as ssh

from server import FakeSFTPServer


class AttrHolder(object):
    pass


def test_list_folder_in_homedir():
    for desc, file_map, expected in (
        (
            "Single file",
            {'file.txt': 'contents'},
            ['file.txt']
        ),
        (
            "Multiple files",
            {'file1.txt': 'contents', 'file2.txt': 'contents2'},
            ['file1.txt', 'file2.txt']
        ),
        (
            "Single empty folder",
            {'folder': None},
            ['folder']
        ),
        (
            "Empty subfolders",
            {'folder/subfolder': None},
            ['folder']
        ),
        (
            "Mixed files, folders empty and non-empty",
            {
                'file.txt': 'contents',
                'file2.txt': 'contents2',
                'folder/file3.txt': 'contents3',
                'empty_folder': None
            },
            ['file.txt', 'file2.txt', 'folder', 'empty_folder']
        ),
    ):
        # Pass in fake server obj. (Can't easily clean up API to be more
        # testable since it's all implementing Paramiko interface stuff.)
        server = AttrHolder()
        server.files = file_map
        interface = FakeSFTPServer(server)
        # list_folder("") uses implicit homedir, as do all inputs
        results = interface.list_folder("")
        # In this particular suite of tests, all results should be a file list,
        # not "no files found"
        ok_(results != ssh.SFTP_NO_SUCH_FILE)
        # Grab filename from SFTPAttribute objects in result
        output = map(lambda x: x.filename, results)
        # Yield test generator
        eq_.description = "list_folder (home dir paths): %s" % desc
        yield eq_, set(expected), set(output)
        del eq_.description
