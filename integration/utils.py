import os
import sys

# Pull in regular tests' utilities
mod = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tests'))
sys.path.insert(0, mod)
from mock_streams import mock_streams
#from utils import FabricTest
# Clean up
del sys.path[0]


class Integration(object):
    def setup(self):
        # Just so subclasses can super() us w/o fear. Meh.
        pass

    def teardown(self):
        # Just so subclasses can super() us w/o fear. Meh.
        pass
