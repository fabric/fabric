"""
Internal shared-state variables such as config settings and host lists.
"""
from __future__ import absolute_import
import sys

from swatch.utils import AliasDict, AttributeDict

win32 = (sys.platform == 'win32')
"""
Options/settings which exist both as environment keys and which can be set on
the command line, are defined here. When used via `fab` they will be added to
the optparse parser, and either way they are added to `env` below (i.e.  the
'dest' value becomes the environment key and the value, the env value).

Keep in mind that optparse changes hyphens to underscores when automatically
deriving the `dest` name, e.g. `--reject-unknown-hosts` becomes
`reject_unknown_hosts`.

Furthermore, *always* specify some sort of default to avoid ending up with
optparse.NO_DEFAULT (currently a two-tuple)! In general, None is a better
default than ''.

User-facing documentation for these are kept in sites/docs/env.rst.


Environment dictionary - actual dictionary object


Global environment dict. Currently a catchall for everything: config settings
such as global deep/broad mode, host lists, username etc.
Most default values are specified in `env_options` above, in the interests of
preserving DRY: anything in here is generally not settable via the command
line.
"""
env = AttributeDict({
    'abort_exception': None,
    'again_prompt': 'Sorry, try again.',
    'all_hosts': [],
    'combine_stderr': True,
    'colorize_errors': False,
    'command': None,
    'command_prefixes': [],
    'cwd': '',  # Must be empty string, not None, for concatenation purposes
    'dedupe_hosts': True,
    'eagerly_disconnect': False,
    'echo_stdin': True,
    'effective_roles': [],
    'exclude_hosts': [],
    'gateway': None,
    'host': None,
    'host_string': None,
    'lcwd': '',  # Must be empty string, not None, for concatenation purposes
    'output_prefix': True,
    'passwords': {},
    'path': '',
    'path_behavior': 'append',
    'real_fabfile': None,
    'remote_interrupt': None,
    'roles': [],
    'roledefs': {},
    'shell_env': {},
    'skip_bad_hosts': False,
    'skip_unknown_tasks': False,
    'ok_ret_codes': [0],  # a list of return codes that indicate success
    # -S so sudo accepts passwd via stdin, -p with our known-value prompt for
    # later detection (thus %s -- gets filled with env.sudo_prompt at runtime)
    'sudo_prefix': "sudo -S -p '%(sudo_prompt)s' ",
    'sudo_prompt': 'sudo password:',
    'sudo_user': None,
    'tasks': [],
    'prompts': {},
    'use_exceptions_for': {'network': False},
    'use_shell': True,
    'use_ssh_config': False,
    'user': None,
})

# Fill in exceptions settings
exceptions = ['network']
exception_dict = {}
for e in exceptions:
    exception_dict[e] = False
env.use_exceptions_for = AliasDict(exception_dict,
                                   aliases={'everything': exceptions})

# Add in option defaults
# for option in env_options:
# env[option.dest] = option.default

#
# Command dictionary
#

# Keys are the command/function names, values are the callables themselves.
# This is filled in when main() runs.
commands = {}
"""
Output controls


Keys are "levels" or "groups" of output, values are always boolean,
determining whether output falling into the given group is printed or not
printed.

By default, everything except 'debug' is printed, as this is what the average
user, and new users, are most likely to expect.

See docs/usage.rst for details on what these levels mean."""
output = AliasDict({
    'status': True,
    'aborts': True,
    'warnings': True,
    'running': True,
    'stdout': True,
    'stderr': True,
    'debug': False,
    'user': True
},
                   aliases={
                       'everything': ['warnings', 'running', 'user', 'output'],
                       'output': ['stdout', 'stderr'],
                       'commands': ['stdout', 'running']
                   })
