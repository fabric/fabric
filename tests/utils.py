"""
Tests testing the fabric.utils module, not utils for the tests!
"""

# TODO: skip on Windows CI, it may blow up on one of these
import fcntl
import termios

from mock import patch
from spec import Spec, eq_, skip

from fabric.utils import get_local_user, get_pty_size


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

    # TODO: test for ImportError+win32 once appveyor is set up as w/ invoke


class pty_size(Spec):
    # TODO: Windows tests under appveyor

    @patch('fcntl.ioctl', wraps=fcntl.ioctl)
    def calls_fcntl_with_TIOCGWINSZ(self, ioctl):
        # Test the default (Unix) implementation because that's all we can
        # realistically do here.
        get_pty_size()
        eq_(ioctl.call_args_list[0][0][1], termios.TIOCGWINSZ)

    def defaults_to_80x24_when_stdout_lacks_fileno(self):
        # i.e. when accessing it throws AttributeError
        skip()

    def defaults_to_80x24_when_stdout_not_a_tty(self):
        # i.e. when os.isatty(sys.stdout) is False
        skip()
