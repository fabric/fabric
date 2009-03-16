from nose.tools import eq_, with_setup
from fudge import with_patched_object, with_fakes, Fake, clear_expectations

from fabric.network import HostConnectionCache, join_host_strings, normalize
from fabric.utils import get_system_username
import fabric.network # So I can call with_patched_object correctly. Sigh.


def test_host_string_normalization():
    username = get_system_username()
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


@with_fakes
@with_patched_object('fabric.network', 'connect', 
    Fake('connect', expect_call=True).times_called(2)
)
def test_no_connection_caching():
    cache = HostConnectionCache()
    # Prime with one connection
    conn1 = cache['localhost']
    # Add another different one (so, connect() is called 2x total)
    conn2 = cache['other-system']
test_no_connection_caching.setup = clear_expectations


@with_fakes
@with_patched_object('fabric.network', 'connect',
    Fake('connect', expect_call=True).calls(join_host_strings).times_called(1)
)
def test_connection_caching():
    cache = HostConnectionCache()
    # Prime with one connection
    conn1 = cache['localhost']
    # And get that same connection again (so connect() called once only)
    conn2 = cache['localhost']
test_connection_caching.setup = clear_expectations
