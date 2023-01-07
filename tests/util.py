"""
Tests testing the fabric.util module, not utils for the tests!
"""

from unittest.mock import patch

from fabric.util import get_local_user


# Basically implementation tests, because it's not feasible to do a "real" test
# on random platforms (where we have no idea what the actual invoking user is)
class get_local_user_:
    @patch("getpass.getuser")
    def defaults_to_getpass_getuser(self, getuser):
        "defaults to getpass.getuser"
        get_local_user()
        getuser.assert_called_once_with()

    @patch("getpass.getuser", side_effect=KeyError)
    def KeyError_means_SaaS_and_thus_None(self, getuser):
        assert get_local_user() is None

    # TODO: test for ImportError+win32 once appveyor is set up as w/ invoke
