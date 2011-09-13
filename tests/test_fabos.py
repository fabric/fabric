#test_fabos.py

from __future__ import with_statement

from fabric.api import hide, get, show, run
from fabric.contrib.fab_os import * 

from utils import FabricTest, eq_contents
from fabric.state import env, output
from server import server

class TestFabOs(FabricTest):

    def test_os(self):
        """
        Verify output of standard os library

        If any of these asserts FAIL then the assumptions
        taken when creating fabos are wrong/need updating
        """
    
        # Create file for tests
        from tempfile import TemporaryFile, mkdtemp
        import os
        
        f = TemporaryFile()
        assert os.path.isfile(f.name) == True
        assert os.path.isfile('/thisshouldneverexists') == False

        assert os.path.isdir(f.name) == False
        assert os.path.isdir('/thisshouldneverexists') == False

        d = mkdtemp()
        assert os.path.isfile(d) == False
        assert os.path.isdir(d) == True
        assert os.rmdir(d) == None
        assert os.path.isdir(d) == False

    @server(responses={"stat -Lc '%F' '/file.txt'":'regular file',
            'test -e "/file.txt"':"",
            "stat -Lc '%F' '/'":'directory',
            'test -e "/"':"",
            "stat -Lc '%F' 'junk'":"stat: cannot stat `junk'",
            'test -e "junk"':""
    })
    def test_isfile(self):
        """
        isfile() returns string 'regular file'
        """
        # Object is a file
        assert isfile('/file.txt') == True
        # Object is a dir
        assert isfile('/') == False
        # Object doesn't exist 
        assert isfile('junk') == False

    @server(responses={"stat -Lc '%F' '/file.txt'":'regular file',
            'test -e "/file.txt"':"",
            "stat -Lc '%F' '/'":'directory',
            'test -e "/"':"",
            "stat -Lc '%F' 'junk'":"stat: cannot stat `junk'",
            'test -e "junk"':""
    })
    def test_isdir(self):
        """
        isdir() returns string 'directory'
        """
        # Object is a file
        assert isdir('/file.txt') == False
        # Object is a dir 
        assert isdir('/') == True
        # Object doesn't exist 
        assert isdir('junk') == False


    @server(responses={
            "stat -Lc '%F' '/file.txt'":'regular file',
            'test -e "/file.txt"':"",
            "stat -c '%a %i %d %h %u %g %o %X %Y %Z' '/file.txt'":"775 156169 51713 2 502 503 4096 1315014048 1315017190 1315017193",
            "stat -Lc '%F' 'junk'":"stat: cannot stat `junk'",
            'test -e "junk"':["","",-1]
    })
    def test_stat(self):
        """
        stat()
        """
        file_obj = stat('/file.txt')
        assert file_obj.st_ino == 156169
        assert file_obj.st_dev == 51713
        assert file_obj.st_nlink == 2

        assert file_obj.st_uid != '502'
        assert file_obj.st_uid == 502

        assert file_obj.st_gid != '503'
        assert file_obj.st_gid == 503

        assert file_obj.st_size == 4096
        assert file_obj.st_atime == 1315014048
        assert file_obj.st_mtime == 1315017190
        assert file_obj.st_ctime == 1315017193

        try:
            nonexistent = stat('junk')
        except OSError, ex:
            assert ex.strerror == "No such file or directory"
            assert ex.errno == 2
            assert ex.filename == 'junk' 
