from __future__ import with_statement

from datetime import datetime
import getpass
import sys

import paramiko
from nose.tools import eq_, with_setup
from fudge import Fake, clear_calls, clear_expectations, patch_object, verify, \
    with_patched_object, patched_context

from fabric.network import (HostConnectionCache, join_host_strings, normalize,
    denormalize, output_thread)
import fabric.network # So I can call patch_object correctly. Sigh.
from fabric.state import env, _get_system_username, output as state_output

from utils import mock_streams


#
# Subroutines, e.g. host string normalization
#

def test_host_string_normalization():
    username = _get_system_username()
    for description, input, output in (
        ("Sanity check: equal strings remain equal",
            'localhost', 'localhost'),
        ("Empty username is same as get_system_username",
            'localhost', username + '@localhost'),
        ("Empty port is same as port 22",
            'localhost', 'localhost:22'),
        ("Both username and port tested at once, for kicks",
            'localhost', username + '@localhost:22'),
    ):
        eq_.description = "Host-string normalization: %s" % description
        yield eq_, normalize(input), normalize(output)
        del eq_.description

def test_normalization_without_port():
    """
    normalize() and join_host_strings() omit port if omit_port given
    """
    eq_(
        join_host_strings(*normalize('user@localhost', omit_port=True)),
        'user@localhost'
    )

def test_nonword_character_in_username():
    """
    normalize() will accept non-word characters in the username part
    """
    eq_(
        normalize('user-with-hyphens@someserver.org')[0],
        'user-with-hyphens'
    )

def test_normalization_of_empty_input():
    empties = ('', '', '')
    for description, input in (
        ("empty string", ''),
        ("None", None)
    ):
        eq_.description = "normalize() returns empty strings for %s input" % (
            description
        )
        yield eq_, normalize(input), empties
        del eq_.description

def test_host_string_denormalization():
    username = _get_system_username()
    for description, string1, string2 in (
        ("Sanity check: equal strings remain equal",
            'localhost', 'localhost'),
        ("Empty username is same as get_system_username",
            'localhost:22', username + '@localhost:22'),
        ("Empty port is same as port 22",
            'user@localhost', 'user@localhost:22'),
        ("Both username and port",
            'localhost', username + '@localhost:22'),
    ):
        eq_.description = "Host-string denormalization: %s" % description
        yield eq_, denormalize(string1), denormalize(string2) 
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


#
# Connection loop flow
#

def test_saved_authentication_returns_client_object():
    # Fake client whose connect() doesn't raise any errors.
    # Note that we don't need verify/clear_calls/etc as this Fake isn't
    # expecting anything.
    f = (
        Fake('SSHClient')
        .provides('__init__')
        .provides('connect')
        .provides('load_system_host_keys')
        .provides('set_missing_host_key_policy')
    )
    with patched_context('paramiko', 'SSHClient', f):
        # Any connection attempts will "succeed" and return the client object
        cache = HostConnectionCache()
        eq_(cache['localhost'], f)

def test_prompts_for_password_without_good_authentication():
    # Fake client whose connect() raises an AuthenticationException on first
    # call, mimicing behavior when auth is bad or doesn't exist yet
    f = (
        Fake('SSHClient')
        .provides('__init__')
        .provides('connect').raises(
            paramiko.AuthenticationException
        ).next_call().returns(True)
        .provides('load_system_host_keys')
        .provides('set_missing_host_key_policy')
    )
    with patched_context('paramiko', 'SSHClient', f):
        # Fake builtin getpass() method which expects to be called once
        f2 = Fake('getpass', expect_call=True).times_called(1).returns('passwd')
        with patched_context('getpass', 'getpass', f2):
            try:
                # Connect attempt will result in getpass() being called
                cache = HostConnectionCache()
                cache['localhost']
                verify()
            finally:
                clear_expectations()


class FakeChannel(object):
    """
    Does what it says on the tin. Fakes a paramiko.Channel object.

    Currently only fakes what is necessary for the following test and is not a
    full drop-in replacement.
    """
    def __init__(self, stdout_text, stderr_text=""):
        self.stdout = stdout_text
        self.stderr = stderr_text

    def _recv(self, which, num_bytes):
        obj = getattr(self, which)
        chunk = obj[:num_bytes]
        setattr(self, which, obj[num_bytes:])
        return chunk

    def recv(self, num_bytes):
        return self._recv('stdout', num_bytes)

    def recv_stderr(self, num_bytes):
        return self._recv('stderr', num_bytes)


@mock_streams('stdout')
def test_trailing_newline_line_drop():
    """
    Trailing newlines shouldn't cause last line to be dropped.
    """
    # Multiline output with trailing newline
    output_string = """AUTHORS
FAQ
Fabric.egg-info
INSTALL
LICENSE
MANIFEST
README
build
docs
fabfile.py
fabfile.pyc
fabric
requirements.txt
setup.py
tests
"""
    # Setup for calling output_thread
    capture = []
    prefix = "[localhost]"
    # TODO: fix below two lines, duplicates inner workings of output_thread
    full_prefix = prefix + ": "
    expected_output = (full_prefix
        + ('\n' + full_prefix).join(output_string.splitlines())
    ) + '\n'
    # Create, tie off thread
    thread = output_thread(prefix, FakeChannel(output_string), capture=capture)
    thread.join()
    # Test equivalence of expected, received output
    eq_(
        expected_output,
        sys.stdout.getvalue()
    )
