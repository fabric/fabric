from nose.tools import eq_

from fabric.state import _HostConnectionCache
from fabric.utils import get_system_username


#
# Initialization (no need for actual setup function for these)
#

username = get_system_username()
normalize = _HostConnectionCache.normalize


def test_host_string_normalization():
    for s1, s2 in [
        # Basic
        ('localhost', 'localhost'),
        # Username
        ('localhost', username + '@localhost'),
        # Port
        ('localhost', 'localhost:22'),
        # Both username and port
        ('localhost', username + '@localhost:22')
    ]:
        yield eq_, normalize(s1), normalize(s2) 
