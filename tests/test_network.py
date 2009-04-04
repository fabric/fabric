from __future__ import with_statement

from datetime import datetime

from nose.tools import eq_, with_setup
from fudge import Fake, clear_calls, clear_expectations, patch_object, verify

from fabric.network import HostConnectionCache, join_host_strings, normalize
from fabric.utils import get_system_username
import fabric.network # So I can call patch_object correctly. Sigh.


#
# Subroutines, e.g. host string normalization
#

def test_host_string_normalization():
    username = get_system_username()
    for description, string1, string2 in (
        ("Sanity check: equal strings remain equal",
            'localhost', 'localhost'),
        ("Empty username is same as get_system_username",
            'localhost', username + '@localhost'),
        ("Empty port is same as port 22",
            'localhost', 'localhost:22'),
        ("Both username and port tested at once, for kicks",
            'localhost', username + '@localhost:22'),
    ):
        eq_.description = description
        yield eq_, normalize(string1), normalize(string2) 
        del eq_.description


#
# Connection caching
#

def check_connection_calls(host_strings, num_calls):
    # Clear Fudge call stack
    clear_calls()
    # Patch connect() with Fake obj set to expect num_calls calls
    patched_connect = patch_object('fabric.network', 'connect',
        Fake('connect', expect_call=True).times_called(num_calls)
    )
    try:
        # Make new cache object
        cache = HostConnectionCache()
        # Connect to all connection strings
        for host_string in host_strings:
            # Obtain connection from cache, potentially calling connect()
            cache[host_string]
        # Verify expected calls matches up with actual calls
        verify()
    finally:
        # Restore connect()
        patched_connect.restore()
        # Clear expectation stack
        clear_expectations()

def test_connection_caching():
    for description, host_strings, num_calls in (
        ("Two different host names, two connections",
            ('localhost', 'other-system'), 2),
        ("Same host twice, one connection",
            ('localhost', 'localhost'), 1),
        ("Same host twice, different ports, two connections",
            ('localhost:22', 'localhost:222'), 2),
        ("Same host twice, different users, two connections",
            ('user1@localhost', 'user2@localhost'), 2),
    ):
        check_connection_calls.description = description
        yield check_connection_calls, host_strings, num_calls
