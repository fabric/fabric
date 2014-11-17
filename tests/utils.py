"""
Tests testing the fabric.utils module, not utils for the tests!
"""

from mock import patch
from spec import Spec, eq_, skip

from fabric.utils import get_local_user


# Basically implementation tests, because it's not feasible to do a "real" test
# on random platforms (where we have no idea what the actual invoking user is)
class get_local_user_(Spec):
    @patch('getpass.getuser')
    def defaults_to_getpass_getuser(self, getuser):
        "defaults to getpass.getuser"
        get_local_user()
        getuser.assert_called_once_with()

    @patch('getpass.getuser', side_effect=KeyError)
    def KeyError_means_SaaS_and_thus_None(self, getuser):
        eq_(get_local_user(), None)

    # TODO: if we find a way to run on a Windows CI environment, test for
    # ImportError+win32.
