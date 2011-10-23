from __future__ import with_statement

from datetime import datetime
import copy
import getpass
import sys

import ssh
from nose.tools import with_setup, ok_
from fudge import (Fake, clear_calls, clear_expectations, patch_object, verify,
    with_patched_object, patched_context, with_fakes)

from fabric.context_managers import settings, hide, show
from fabric.network import (HostConnectionCache, join_host_strings, normalize,
    denormalize)
from fabric.io import output_loop
import fabric.network  # So I can call patch_object correctly. Sigh.
from fabric.state import env, output, _get_system_username
from fabric.operations import run, sudo, prompt

from utils import *
from server import (server, PORT, RESPONSES, PASSWORDS, CLIENT_PRIVKEY, USER,
    CLIENT_PRIVKEY_PASSPHRASE)


#
# Subroutines, e.g. host string normalization
#


class TestNetwork(FabricTest):
    def test_host_string_normalization(self):
        username = _get_system_username()
        for description, input, output_ in (
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
            yield eq_, normalize(input), normalize(output_)
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

    def test_at_symbol_in_username(self):
        """
        normalize() should allow '@' in usernames (i.e. last '@' is split char)
        """
        parts = normalize('user@example.com@www.example.com')
        eq_(parts[0], 'user@example.com')
        eq_(parts[1], 'www.example.com')

    def test_normalization_of_empty_input(self):
        empties = ('', '', '')
        for description, input in (
            ("empty string", ''),
            ("None", None)
        ):
            template = "normalize() returns empty strings for %s input"
            eq_.description = template % description
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
    @with_fakes
    def check_connection_calls(host_strings, num_calls):
        # Clear Fudge call stack
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
        finally:
            # Restore connect()
            patched_connect.restore()

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

    def test_connection_cache_deletion(self):
        """
        HostConnectionCache should delete correctly w/ non-full keys
        """
        hcc = HostConnectionCache()
        fake = Fake('connect', callable=True)
        with patched_context('fabric.network', 'connect', fake):
            for host_string in ('hostname', 'user@hostname',
                'user@hostname:222'):
                # Prime
                hcc[host_string]
                # Test
                ok_(host_string in hcc)
                # Delete
                del hcc[host_string]
                # Test
                ok_(host_string not in hcc)


    #
    # Connection loop flow
    #
    @server()
    def test_saved_authentication_returns_client_object(self):
        cache = HostConnectionCache()
        assert isinstance(cache[env.host_string], ssh.SSHClient)

    @server()
    @with_fakes
    def test_prompts_for_password_without_good_authentication(self):
        env.password = None
        with password_response(PASSWORDS[env.user], times_called=1):
            cache = HostConnectionCache()
            cache[env.host_string]


    @aborts
    def test_aborts_on_prompt_with_abort_on_prompt(self):
        """
        abort_on_prompt=True should abort when prompt() is used
        """
        env.abort_on_prompts = True
        prompt("This will abort")


    @server()
    @aborts
    def test_aborts_on_password_prompt_with_abort_on_prompt(self):
        """
        abort_on_prompt=True should abort when password prompts occur
        """
        env.password = None
        env.abort_on_prompts = True
        with password_response(PASSWORDS[env.user], times_called=1):
            cache = HostConnectionCache()
            cache[env.host_string]


    @mock_streams('stdout')
    @server()
    def test_does_not_abort_with_password_and_host_with_abort_on_prompt(self):
        """
        abort_on_prompt=True should not abort if no prompts are needed
        """
        env.abort_on_prompts = True
        env.password = PASSWORDS[env.user]
        # env.host_string is automatically filled in when using server()
        run("ls /simple")


    @mock_streams('stdout')
    @server()
    def test_trailing_newline_line_drop(self):
        """
        Trailing newlines shouldn't cause last line to be dropped.
        """
        # Multiline output with trailing newline
        cmd = "ls /"
        output_string = RESPONSES[cmd]
        # TODO: fix below lines, duplicates inner workings of tested code
        prefix = "[%s] out: " % env.host_string
        expected = prefix + ('\n' + prefix).join(output_string.split('\n'))
        # Create, tie off thread
        with settings(show('everything'), hide('running')):
            result = run(cmd)
            # Test equivalence of expected, received output
            eq_(expected, sys.stdout.getvalue())
            # Also test that the captured value matches, too.
            eq_(output_string, result)

    @server()
    def test_sudo_prompt_kills_capturing(self):
        """
        Sudo prompts shouldn't screw up output capturing
        """
        cmd = "ls /simple"
        with hide('everything'):
            eq_(sudo(cmd), RESPONSES[cmd])

    @server()
    def test_password_memory_on_user_switch(self):
        """
        Switching users mid-session should not screw up password memory
        """
        def _to_user(user):
            return join_host_strings(user, env.host, env.port)

        user1 = 'root'
        user2 = USER
        with settings(hide('everything'), password=None):
            # Connect as user1 (thus populating both the fallback and
            # user-specific caches)
            with settings(
                password_response(PASSWORDS[user1]),
                host_string=_to_user(user1)
            ):
                run("ls /simple")
            # Connect as user2: * First cxn attempt will use fallback cache,
            # which contains user1's password, and thus fail * Second cxn
            # attempt will prompt user, and succeed due to mocked p4p * but
            # will NOT overwrite fallback cache
            with settings(
                password_response(PASSWORDS[user2]),
                host_string=_to_user(user2)
            ):
                # Just to trigger connection
                run("ls /simple")
            # * Sudo call should use cached user2 password, NOT fallback cache,
            # and thus succeed. (I.e. p_f_p should NOT be called here.)
            with settings(
                password_response('whatever', times_called=0),
                host_string=_to_user(user2)
            ):
                sudo("ls /simple")

    @mock_streams('stderr')
    @server()
    def test_password_prompt_displays_host_string(self):
        """
        Password prompt lines should include the user/host in question
        """
        env.password = None
        env.no_agent = env.no_keys = True
        output.everything = False
        with password_response(PASSWORDS[env.user], silent=False):
            run("ls /simple")
        regex = r'^\[%s\] Login password: ' % env.host_string
        assert_contains(regex, sys.stderr.getvalue())

    @mock_streams('stderr')
    @server(pubkeys=True)
    def test_passphrase_prompt_displays_host_string(self):
        """
        Passphrase prompt lines should include the user/host in question
        """
        env.password = None
        env.no_agent = env.no_keys = True
        env.key_filename = CLIENT_PRIVKEY
        output.everything = False
        with password_response(CLIENT_PRIVKEY_PASSPHRASE, silent=False):
            run("ls /simple")
        regex = r'^\[%s\] Login password: ' % env.host_string
        assert_contains(regex, sys.stderr.getvalue())

    def test_sudo_prompt_display_passthrough(self):
        """
        Sudo prompt should display (via passthrough) when stdout/stderr shown
        """
        TestNetwork._prompt_display(True)

    def test_sudo_prompt_display_directly(self):
        """
        Sudo prompt should display (manually) when stdout/stderr hidden
        """
        TestNetwork._prompt_display(False)

    @staticmethod
    @mock_streams('both')
    @server(pubkeys=True, responses={'oneliner': 'result'})
    def _prompt_display(display_output):
        env.password = None
        env.no_agent = env.no_keys = True
        env.key_filename = CLIENT_PRIVKEY
        output.output = display_output
        with password_response(
            (CLIENT_PRIVKEY_PASSPHRASE, PASSWORDS[env.user]),
            silent=False
        ):
            sudo('oneliner')
        if display_output:
            expected = """
[%(prefix)s] sudo: oneliner
[%(prefix)s] Login password: 
[%(prefix)s] out: sudo password:
[%(prefix)s] out: Sorry, try again.
[%(prefix)s] out: sudo password: 
[%(prefix)s] out: result
""" % {'prefix': env.host_string}
        else:
            # Note lack of first sudo prompt (as it's autoresponded to) and of
            # course the actual result output.
            expected = """
[%(prefix)s] sudo: oneliner
[%(prefix)s] Login password: 
[%(prefix)s] out: Sorry, try again.
[%(prefix)s] out: sudo password: """ % {'prefix': env.host_string}
        eq_(expected[1:], sys.stdall.getvalue())

    @mock_streams('both')
    @server(
        pubkeys=True,
        responses={'oneliner': 'result', 'twoliner': 'result1\nresult2'}
    )
    def test_consecutive_sudos_should_not_have_blank_line(self):
        """
        Consecutive sudo() calls should not incur a blank line in-between
        """
        env.password = None
        env.no_agent = env.no_keys = True
        env.key_filename = CLIENT_PRIVKEY
        with password_response(
            (CLIENT_PRIVKEY_PASSPHRASE, PASSWORDS[USER]),
            silent=False
        ):
            sudo('oneliner')
            sudo('twoliner')
        expected = """
[%(prefix)s] sudo: oneliner
[%(prefix)s] Login password: 
[%(prefix)s] out: sudo password:
[%(prefix)s] out: Sorry, try again.
[%(prefix)s] out: sudo password: 
[%(prefix)s] out: result
[%(prefix)s] sudo: twoliner
[%(prefix)s] out: sudo password:
[%(prefix)s] out: result1
[%(prefix)s] out: result2
""" % {'prefix': env.host_string}
        eq_(expected[1:], sys.stdall.getvalue())

    @mock_streams('both')
    @server(pubkeys=True, responses={'silent': '', 'normal': 'foo'})
    def test_silent_commands_should_not_have_blank_line(self):
        """
        Silent commands should not generate an extra trailing blank line

        After the move to interactive I/O, it was noticed that while run/sudo
        commands which had non-empty stdout worked normally (consecutive such
        commands were totally adjacent), those with no stdout (i.e. silent
        commands like ``test`` or ``mkdir``) resulted in spurious blank lines
        after the "run:" line. This looks quite ugly in real world scripts.
        """
        env.password = None
        env.no_agent = env.no_keys = True
        env.key_filename = CLIENT_PRIVKEY
        with password_response(CLIENT_PRIVKEY_PASSPHRASE, silent=False):
            run('normal')
            run('silent')
            run('normal')
            with hide('everything'):
                run('normal')
                run('silent')
        expected = """
[%(prefix)s] run: normal
[%(prefix)s] Login password: 
[%(prefix)s] out: foo
[%(prefix)s] run: silent
[%(prefix)s] run: normal
[%(prefix)s] out: foo
""" % {'prefix': env.host_string}
        eq_(expected[1:], sys.stdall.getvalue())

    @mock_streams('both')
    @server(
        pubkeys=True,
        responses={'oneliner': 'result', 'twoliner': 'result1\nresult2'}
    )
    def test_io_should_print_prefix_if_ouput_prefix_is_true(self):
        """
        run/sudo should print [host_string] if env.output_prefix == True
        """
        env.password = None
        env.no_agent = env.no_keys = True
        env.key_filename = CLIENT_PRIVKEY
        with password_response(
            (CLIENT_PRIVKEY_PASSPHRASE, PASSWORDS[USER]),
            silent=False
        ):
            run('oneliner')
            run('twoliner')
        expected = """
[%(prefix)s] run: oneliner
[%(prefix)s] Login password: 
[%(prefix)s] out: result
[%(prefix)s] run: twoliner
[%(prefix)s] out: result1
[%(prefix)s] out: result2
""" % {'prefix': env.host_string}
        eq_(expected[1:], sys.stdall.getvalue())

    @mock_streams('both')
    @server(
        pubkeys=True,
        responses={'oneliner': 'result', 'twoliner': 'result1\nresult2'}
    )
    def test_io_should_not_print_prefix_if_ouput_prefix_is_false(self):
        """
        run/sudo shouldn't print [host_string] if env.output_prefix == False
        """
        env.password = None
        env.no_agent = env.no_keys = True
        env.key_filename = CLIENT_PRIVKEY
        with password_response(
            (CLIENT_PRIVKEY_PASSPHRASE, PASSWORDS[USER]),
            silent=False
        ):
            with settings(output_prefix=False):
                run('oneliner')
                run('twoliner')
        expected = """
[%(prefix)s] run: oneliner
[%(prefix)s] Login password: 
result
[%(prefix)s] run: twoliner
result1
result2
""" % {'prefix': env.host_string}
        eq_(expected[1:], sys.stdall.getvalue())
