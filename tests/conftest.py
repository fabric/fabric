# flake8: noqa
import sys
from os.path import isfile, expanduser
if sys.version_info[0] == 2:
    from mock import patch
else:
    from unittest.mock import patch

from pytest import fixture

# Set up icecream globally for convenience.
from icecream import install as install_icecream

from fabric.testing.fixtures import client, remote, sftp, sftp_objs, transfer


install_icecream()


# TODO: does this want to end up in the public fixtures module too?
@fixture(autouse=True)
def no_user_ssh_config():
    """
    Cowardly refuse to ever load what looks like user SSH config paths.

    Prevents the invoking user's real config from gumming up test results or
    inflating test runtime (eg if it sets canonicalization on, which will incur
    DNS lookups for nearly all of this suite's bogus names).
    """
    # An ugly, but effective, hack. I am not proud. I also don't see anything
    # that's >= as bulletproof and less ugly?
    # TODO: ideally this should expand to cover system config paths too, but
    # that's even less likely to be an issue.
    def no_config_for_you(path):
        if path == expanduser("~/.ssh/config"):
            return False
        return isfile(path)

    with patch("fabric.config.os.path.isfile", no_config_for_you):
        yield
