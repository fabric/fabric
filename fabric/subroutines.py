"""
Internal subroutines for e.g. aborting execution with an error message,
or handling Fabric-specific string formatting.
"""

from optparse import OptionParser
import os
import re
import sys

from state import env, win32


FORMAT_REGEX = re.compile(r'(\\?)(\$\((?P<var>[\w-]+?)\))')

def format(s):
    """
    Replace "$(foo)" style references to ENV vars in given string, and return
    the result.
    """
    if s is None:
        return None
    # Escape percent signs
    s = s.replace('%', '%%')
    # Function to go from match object => new string
    def func(match):
        escape = match.group(1)
        if escape == '\\':
            return match.group(2)
        var = match.group('var')
        if var in env:
            return escape + format(str(env[var]) % env)
        else:
            return match.group(0)
    return re.sub(FORMAT_REGEX, func, s % env)


def abort(msg):
    """
    Abort execution, printing given message and exiting with error status.
    """
    print("Error: " + format(msg))
    sys.exit(1)


def warn(msg):
    """
    Print warning message, but do not abort execution.
    """
    print("Warning: " + format(msg))


def rc_path():
    """
    Return platform-specific file path for $HOME/<env.settings_file>.
    """
    if not win32:
        return os.path.expanduser("~/" + env.settings_file)
    else:
        from win32com.shell.shell import SHGetSpecialFolderPath
        from win32com.shell.shellcon import CSIDL_PROFILE
        return "%s/%s" % (
            SHGetSpecialFolderPath(0,CSIDL_PROFILE),
            env.settings_file
        )


def load_settings(path):
    """
    Take given file path and apply any key=value pairs to the environment dict.

    Returns True if file exists and data was added (implicit None otherwise).
    """
    if os.path.exists(path):
        comments = lambda s: s and not s.startswith("#")
        settings = filter(comments, open(path, 'r'))
        settings = [(k.strip(), v.strip()) for k, _, v in
            [s.partition('=') for s in settings]]
        if settings:
            env.update(settings)
            return True


def find_fabfile():
    """
    Attempt to locate a fabfile in current or parent directories.

    Fabfiles are defined as files named 'fabfile.py' or 'Fabfile.py'. The '.py'
    extension is required, as fabfile loading (both by 'fab' and by fabfiles
    which need other sub-fabfiles) is done via importing, not exec.

    Order of search is lowercase filename, capitalized filename, in current
    working directory (where 'fab' was invoked) and then each parent directory
    in turn.

    Returns absolute path to first match, or None if no match found.
    """
    guesses = ['fabfile.py', 'Fabfile.py']
    path = '.'
    # Stop before falling off root of filesystem (should be platform agnostic)
    while os.path.split(os.path.abspath(path))[1]:
        found = filter(lambda x: os.path.exists(os.path.join(path, x)), guesses)
        if found:
            return os.path.abspath(os.path.join(path, found[0]))
        path = os.path.join('..', path)


def parse_options():
    """
    Handle command-line options with optparse.OptionParser.

    Return list of arguments, largely for use in parse_arguments().
    """
    #
    # Initialize
    #

    parser = OptionParser(usage="fab [options] <command>[:arg1,arg2=val2,host=foo,hosts='h1;h2',...] ...")

    #
    # Define options
    #

    # Version number (optparse gives you --version but we have to do it
    # ourselves to get -V too. sigh)
    parser.add_option('-V', '--version',
        action='store_true',
        dest='show_version',
        default=False,
        help="show program's version number and exit"
    )

    # List possible Fab commands
    parser.add_option('-l', '--list',
        action='store_true',
        dest='list_commands',
        default=False,
        help="print list of possible commands and exit"
    )

    # TODO: help (and argument signatures?) for a specific command
    # (or allow option-arguments to -h/--help? e.g. "fab -h foo" = help for foo)

    # TODO: verbosity selection (sets state var(s) used when printing)
    # -v / --verbose

    # TODO: specify nonstandard fabricrc file (and call load_settings() on it)
    # -f / --fabricrc ?

    # TODO: old 'let' functionality, i.e. global env additions/overrides
    # maybe "set" as the keyword? i.e. -s / --set x=y
    # allow multiple times (like with tar --exclude)

    # TODO: old 'shell' functionality. Feels kind of odd as an option, but also
    # doesn't make any sense as an actual command (since you cannot run it with
    # other commands at the same time).
    # Probably only offer long option: --shell, possibly with -S for short?

    #
    # Finalize
    #

    # Returns two-tuple, (options, args)
    return parser.parse_args()


def parse_arguments(args):
    """
    Parses the given list of arguments into command names and, optionally,
    per-command args/kwargs. Per-command args are attached to the command name
    with a colon (:), are comma-separated, and may use a=b syntax for kwargs.
    These args/kwargs are passed into the resulting command as normal Python
    args/kwargs.

    For example:

        $ fab do_stuff:a,b,c=d

    will result in the function call do_stuff(a, b, c=d).

    If 'host' or 'hosts' kwargs are given, they will be used to fill Fabric's
    host list (which is checked later on). 'hosts' will override 'host' if both
    are given.
    
    When using 'hosts' in this way, one must use semicolons (;), and must thus
    quote the host list string to prevent shell interpretation.

    For example,

        $ fab ping_servers:hosts="a;b;c",foo=bar

    will result in Fabric's host list for the 'ping_servers' command being set
    to ['a', 'b', 'c'].
    
    'host'/'hosts' are removed from the kwargs mapping at this point, so
    commands are not required to expect them. Thus, the resulting call of the
    above example would be ping_servers(foo=bar).
    """
    cmds = []
    for cmd in args:
        cmd_args = []
        cmd_kwargs = {}
        cmd_hosts = []
        if ':' in cmd:
            cmd, cmd_str_args = cmd.split(':', 1)
            for cmd_arg_kv in cmd_str_args.split(','):
                k, _, v = partition(cmd_arg_kv, '=')
                if v:
                    # Catch, interpret host/hosts kwargs
                    if k in ['host', 'hosts']:
                        if k == 'host':
                            cmd_hosts = [v.strip()]
                        elif k == 'hosts':
                            cmd_hosts = [x.strip() for x in v.split(';')]
                    # Otherwise, record as usual
                    else:
                        cmd_kwargs[k] = (v % ENV) or k
                else:
                    cmd_args.append(k)
        cmds.append((cmd, cmd_args, cmd_kwargs, cmd_hosts))
    return cmds


