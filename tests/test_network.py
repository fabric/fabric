from __future__ import with_statement

from datetime import datetime
import copy
import getpass
import sys

import paramiko
from nose.tools import eq_, with_setup
from fudge import Fake, clear_calls, clear_expectations, patch_object, verify, \
    with_patched_object, patched_context

from fabric.context_managers import settings, hide, show
from fabric.network import (HostConnectionCache, join_host_strings, normalize,
    denormalize, interpret_host_string)
from fabric.io import output_loop
import fabric.network # So I can call patch_object correctly. Sigh.
from fabric.state import env, _get_system_username, output as state_output
from fabric.operations import run, sudo

from utils import mock_streams
from server import server, PORT


#
# Default test server response info
#

mapping = {
    "ls /simple": "some output",
    "ls /": """AUTHORS
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
tests"""
}

users = {
    'root': 'root',
    env.local_user: 'password'
}


#
# Subroutines, e.g. host string normalization
#


class TestNetwork(object):
    def setup(self):
        self.previous_env = copy.deepcopy(env)
        # Network stuff
        env.disable_known_hosts = True
        interpret_host_string('%s@localhost:%s' % (env.local_user, PORT))
        env.password = users[env.local_user]

    def teardown(self):
        env = copy.deepcopy(self.previous_env)

    def test_host_string_normalization(self):
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

    def test_normalization_without_port(self):
        """
        normalize() and join_host_strings() omit port if omit_port given
        """
        eq_(
            join_host_strings(*normalize('user@localhost', omit_port=True)),
            'user@localhost'
        )

    def test_nonword_character_in_username(self):
        """
        normalize() will accept non-word characters in the username part
        """
        eq_(
            normalize('user-with-hyphens@someserver.org')[0],
            'user-with-hyphens'
        )

    def test_normalization_of_empty_input(self):
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

    def test_host_string_denormalization(self):
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

    @staticmethod
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

    def test_connection_caching(self):
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
            TestNetwork.check_connection_calls.description = description
            yield TestNetwork.check_connection_calls, host_strings, num_calls


    #
    # Connection loop flow
    #

    def test_saved_authentication_returns_client_object(self):
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

    def test_prompts_for_password_without_good_authentication(self):
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


    @mock_streams('stdout')
    @server(mapping, users)
    def test_trailing_newline_line_drop(self):
        """
        Trailing newlines shouldn't cause last line to be dropped.
        """
        # Multiline output with trailing newline
        cmd = "ls /"
        output_string = mapping[cmd]
        # TODO: fix below lines, duplicates inner workings of tested code
        prefix = "[%s] out: " % env.host_string
        expected = prefix + ('\n' + prefix).join(output_string.split('\n'))
        # Create, tie off thread
        with settings(show('everything'), hide('running')):
            result = run(cmd, shell=False)
            # Test equivalence of expected, received output
            eq_(expected, sys.stdout.getvalue())
            # Also test that the captured value matches, too.
            eq_(output_string, result)


    @server(mapping, users)
    def test_sudo_prompt_kills_capturing(self):
        """
        Sudo prompts shouldn't screw up output capturing
        """
        cmd = "ls /simple"
        with hide('everything'):
            eq_(sudo(cmd, shell=False), mapping[cmd])


    @server(mapping, users)
    def test_password_memory_on_user_switch(self):
        """
        Switching users mid-session should not screw up password memory
        """
        def _to_user(user):
            return join_host_strings(user, env.host, env.port)

        def _response(response):
            p_f_p = (
                Fake('prompt_for_password', callable=True)
                .next_call().returns(response)
            )
            return patched_context(fabric.network, 'prompt_for_password',
                p_f_p)

        user1 = 'root'
        user2 = env.local_user
        with settings(hide('everything'), password=None):
            # Connect as user1 (thus populating both the fallback and
            # user-specific caches)
            with settings(
                _response(users[user1]),
                host_string=_to_user(user1)
            ):
                run("ls /simple", shell=False)
            # Connect as user2: * First cxn attempt will use fallback cache,
            # which contains user1's password, and thus fail * Second cxn
            # attempt will prompt user, and succeed due to mocked p4p * but
            # will NOT overwrite fallback cache
            with settings(
                _response(users[user2]),
                host_string=_to_user(user2)
            ):
                # Just to trigger connection
                run("ls /simple", shell=False)
            # * Sudo call should use cached user2 password, NOT fallback cache,
            # and thus succeed. (I.e. p_f_p should NOT be called here.)
            p_f_p = Fake(callable=True).times_called(0)
            context = patched_context(fabric.network, 'prompt_for_password',
                p_f_p)
            with settings(context, host_string=_to_user(user2)):
                sudo("ls /simple", shell=False)
