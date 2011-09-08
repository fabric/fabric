from __future__ import with_statement

from fabric.api import hide, get, show, run
from fabric.contrib.fab_os import isfile 

from utils import FabricTest, eq_contents
from fabric.state import env, output
from server import server, FILES



class TestFabOs(FabricTest):
    # Make sure it knows / is a directory.
    # This is in lieu of starting down the "actual honest to god fake operating
    # system" road...:(
    @server(responses={"stat -Lc '%F' '/file.txt'":'regular file',
            'test -e "/file.txt"':""
    })
    def test_isfile(self):
        """
        isfile() returns string 'regular file'
        """
        assert isfile('/file.txt') == True
