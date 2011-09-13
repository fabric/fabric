from __future__ import with_statement

from fabric.api import hide, get, show, run
from fabric.contrib.fab_os import * 

from utils import FabricTest, eq_contents
from fabric.state import env, output
from server import server

class TestFabOs(FabricTest):

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


    @server(responses={"stat -Lc '%F' '/file.txt'":'regular file',
            'test -e "/file.txt"':"",
            "stat -c '%a %i %d %h %u %g %o %X %Y %Z' '/file.txt'":"775 156169 51713 2 502 503 4096 1315014048 1315017193 1315017193"
    })
    def test_stat(self):
        """
        stat()
        """
        file_obj = stat('/file.txt')
        assert file_obj.st_uid != '502'
        assert file_obj.st_uid == 502
