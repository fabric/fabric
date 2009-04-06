"""
This module contains Fab's ``main()`` method plus related subroutines.

``main()`` is executed as the command line ``fab`` program and takes care of
parsing options and commands, loading the user settings file, loading a
fabfile, and executing the commands given.

The other callables defined in this module are internal only. Anything useful
to individuals leveraging Fabric as a library, should be kept elsewhere.
"""

from optparse import OptionParser
import os
import sys

from utils import abort, indent
from state import commands, env, env_options, win32
import operations


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
    Take given file path and return dictionary of any key=value pairs found.
    """
    if os.path.exists(path):
        comments = lambda s: s and not s.startswith("#")
        settings = filter(comments, open(path, 'r'))
        return dict((k.strip(), v.strip()) for k, _, v in
            [s.partition('=') for s in settings])
    # Handle nonexistent or empty settings file
    return {}


def find_fabfile():
    """
    Attempt to locate a fabfile in current or parent directories.

    Fabfiles are defined as files named ``fabfile.py`` or ``Fabfile.py``. The
    ``.py`` extension is required, as fabfile loading (both by ``fab`` and by
    fabfiles which need other sub-fabfiles) is done via importing, not exec.

    Order of search is lowercase filename, capitalized filename, in current
    working directory (where ``fab`` was invoked) and then each parent directory
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


def is_task(func):
    """
    Returns True if ``func`` is callable and not a Fabric operation.
    """
    return callable(func) and (func not in vars(operations).values())


def load_fabfile(path):
    """
    Import given fabfile path and return dictionary of its callables.
    """
    # Get directory and fabfile name
    directory, fabfile = os.path.split(path)
    # If the directory isn't in the PYTHONPATH, add it so our import will work
    added_to_path = False
    if directory not in sys.path:
        sys.path.insert(0, directory)
        added_to_path = True
    # Perform the import (trimming off the .py)
    imported = __import__(os.path.splitext(fabfile)[0])
    # Remove directory from path if we added it ourselves (just to be neat)
    if added_to_path:
        del sys.path[0]
    # Return dictionary of callables only (and don't include Fab operations)
    return dict(filter(lambda x: is_task(x[1]), vars(imported).items()))


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
    # Define options that don't become `env` vars (typically ones which cause
    # Fabric to do something other than its normal execution, such as --version)
    #

    # Version number (optparse gives you --version but we have to do it
    # ourselves to get -V too. sigh)
    parser.add_option('-V', '--version',
        action='store_true',
        dest='show_version',
        default=False,
        help="show program's version number and exit"
    )

    # List Fab commands found in loaded fabfiles/source files
    parser.add_option('-l', '--list',
        action='store_true',
        dest='list_commands',
        default=False,
        help="print list of possible commands and exit"
    )

    # TODO: help (and argument signatures?) for a specific command
    # (or allow option-arguments to -h/--help? e.g. "fab -h foo" = help for foo)

    # TODO: specify nonstandard fabricrc file (and call load_settings() on it)
    # -c ? --config ? --fabricrc ? --rcfile ?
    # what are some commonly used flags for conf file specification?

    # TODO: explicitly specify "fabfile(s)" to load.
    # - Can specify multiple times
    # - Disables implicit "local" fabfile discovery/loading
    #   - or should the default be to "append" to the implicitly loaded fabfile?
    #   - either way, also add a flag to toggle that append/disable behavior
    # Flags: -f ? --fabfile ? --source ? what are some common flags?

    # TODO: old 'let' functionality, i.e. global env additions/overrides
    # maybe "set" as the keyword? i.e. -s / --set x=y
    # allow multiple times (like with tar --exclude)

    # TODO: old 'shell' functionality. Feels kind of odd as an option, but also
    # doesn't make any sense as an actual command (since you cannot run it with
    # other commands at the same time).
    # Probably only offer long option: --shell, possibly with -S for short?

    #
    # Add in options which are also destined to show up as `env` vars.
    #

    for option in env_options:
        parser.add_option(option)

    #
    # Finalize
    #

    # Return three-tuple of parser + the output from parse_args (opt obj, args)
    opts, args = parser.parse_args()
    return parser, opts, args


def list_commands():
    print("Available commands:\n")
    # Want separator between name, description to be straight col
    max_len = reduce(lambda a, b: max(a, len(b)), commands.keys(), 0)
    for name, func in commands.items():
        prefix = '  ' + name.ljust(max_len)
        # Print first line of docstring
        if func.__doc__:
            lines = filter(None, func.__doc__.splitlines())
            print(prefix + '  ' + lines[0].strip())
        # Or nothing (so just the name)
        else:
            print(prefix)
    sys.exit(0)


def parse_arguments(arguments):
    """
    Parse string list into list of 4-tuples: command name, args, kwargs, hosts.

    Parses the given list of arguments into command names and, optionally,
    per-command args/kwargs. Per-command args are attached to the command name
    with a colon (``:``), are comma-separated, and may use a=b syntax for
    kwargs.  These args/kwargs are passed into the resulting command as normal
    Python args/kwargs.

    For example::

        $ fab do_stuff:a,b,c=d

    will result in the function call ``do_stuff(a, b, c=d)``.

    If ``host`` or ``hosts`` kwargs are given, they will be used to fill
    Fabric's host list (which is checked later on). ``hosts`` will override
    ``host`` if both are given.
    
    When using ``hosts`` in this way, one must use semicolons (``;``), and must
    thus quote the host list string to prevent shell interpretation.

    For example::

        $ fab ping_servers:hosts="a;b;c",foo=bar

    will result in Fabric's host list for the ``ping_servers`` command being set
    to ``['a', 'b', 'c']``.
    
    ``host`` and ``hosts`` are removed from the kwargs mapping at this point, so
    commands are not required to expect them. Thus, the resulting call of the
    above example would be ``ping_servers(foo=bar)``.
    """
    cmds = []
    for cmd in arguments:
        args = []
        kwargs = {}
        hosts = []
        if ':' in cmd:
            cmd, argstr = cmd.split(':', 1)
            for pair in argstr.split(','):
                k, _, v = pair.partition('=')
                if v:
                    # Catch, interpret host/hosts kwargs
                    if k in ['host', 'hosts']:
                        if k == 'host':
                            hosts = [v.strip()]
                        elif k == 'hosts':
                            hosts = [x.strip() for x in v.split(';')]
                    # Otherwise, record as usual
                    else:
                        kwargs[k] = v
                else:
                    args.append(k)
        cmds.append((cmd, args, kwargs, hosts))
    return cmds


def get_hosts(cli_hosts, command):
    """
    Return the host list the given command should be using.

    The list of hosts a given command will run on follows a strict order of
    precedence:

    1. Hosts specified via the command line (e.g. ``fab foo:hosts='a;b;c'``)
    2. Hosts specified via the ``@hosts`` decorator (e.g. ``@hosts('a', 'b',
       'c')``)
    3. Hosts specified globally, by setting ``env.hosts`` at module level in
       the fabfile (note: since fabfiles are fully loaded, the last line to set
       ``env.hosts`` is the line that wins)

    If all three sources have been checked and no hosts are found, prompt the
    user for a comma-separated list of host definitions.
    """
    # TODO: Figure out if we should be trying to "merge" host lists when
    # running multiple commands which each specify their own CLI or @hosts list.
    
    if cli_hosts:
        return cli_hosts
    if getattr(command, 'hosts', None):
        return command.hosts
    if env.get('hosts'):
        return env.hosts
    hosts = []
    while not hosts:
        p = "Please specify host or hosts to connect to (comma-separated): "
        hosts = filter(None, raw_input(p).split(','))
    return hosts


def main():
    # We're running from the command line, so set global flag to that effect.
    env.invoked_as_fab = True
    try:
        try:
            # Parse command line options
            parser, options, arguments = parse_options()

            # Handle version number option
            if options.show_version:
                print "Fabric " + env.version
                sys.exit(0)

            # Load settings from user settings file, into shared env dict.
            env.update(load_settings(rc_path()))

            # Find local fabfile path or abort
            fabfile = find_fabfile()
            if not fabfile:
                abort("Couldn't find any fabfiles!")

            # Load fabfile and put its commands in the shared commands dict
            commands.update(load_fabfile(fabfile))

            # Abort if no commands found
            # TODO: continue searching for fabfiles if one we selected doesn't
            # contain any callables? Bit of an edge case, but still...
            if not commands:
                abort("Fabfile didn't contain any commands!")

            # Handle list-commands option (now that commands are loaded)
            if options.list_commands:
                list_commands()

            # If user didn't specify any commands to run, show help
            if not arguments:
                parser.print_help()
                sys.exit(0) # Or should it exit with error (1)?

            # Parse arguments into commands to run (plus args/kwargs/hosts)
            commands_to_run = parse_arguments(arguments)
            
            # Figure out if any specified names are invalid
            unknown_commands = []
            for tup in commands_to_run:
                if tup[0] not in commands:
                    unknown_commands.append(tup[0])

            # Abort if any unknown commands were specified
            if unknown_commands:
                abort("Command(s) not found:\n%s" % indent(unknown_commands))

            # Update env with any overridden option values
            for option in env_options:
                env[option.dest] = getattr(options, option.dest)

            # At this point all commands must exist, so execute them in order.
            for name, args, kwargs, cli_hosts in commands_to_run:
                # Get callable by itself
                command = commands[name]
                # Set current command name (used for some error messages)
                env.command = name
                # Set host list
                hosts = get_hosts(cli_hosts, command)
                # Execute the function on each host in turn
                for host in hosts:
                    env.host = host
                    commands[name](*args, **kwargs)
        finally:
            pass
#            _disconnect()
            print("\nDone.")
    except SystemExit:
        # a number of internal functions might raise this one.
        raise
    except KeyboardInterrupt:
        print("Stopped.")
        sys.exit(1)
    except:
        sys.excepthook(*sys.exc_info())
        # we might leave stale threads if we don't explicitly exit()
        sys.exit(1)
    sys.exit(0)
