from __future__ import with_statement

from fabric.api import hide, get, show, run
from fabric.contrib.fab_os import isfile, isdir

from utils import FabricTest, eq_contents
from fabric.state import env, output
from server import server, FILES

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
