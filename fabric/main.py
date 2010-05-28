"""
This module contains Fab's `main` method plus related subroutines.

`main` is executed as the command line ``fab`` program and takes care of
parsing options and commands, loading the user settings file, loading a
fabfile, and executing the commands given.

The other callables defined in this module are internal only. Anything useful
to individuals leveraging Fabric as a library, should be kept elsewhere.
"""

from operator import add
from optparse import OptionParser
import os
import sys

from fabric import api # For checking callables against the API 
from fabric.contrib import console, files, project # Ditto
from fabric.network import denormalize, normalize
from fabric import state # For easily-mockable access to roles, env and etc
from fabric.state import commands, connections, env_options
from fabric.utils import abort, indent


# One-time calculation of "all internal callables" to avoid doing this on every
# check of a given fabfile callable (in is_task()).
_modules = [api, project, files, console]
_internals = reduce(lambda x, y: x + filter(callable, vars(y).values()),
    _modules,
    []
)

def load_settings(path):
    """
    Take given file path and return dictionary of any key=value pairs found.

    Usage docs are in docs/usage/fab.rst, in "Settings files."
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
    Attempt to locate a fabfile, either explicitly or by searching parent dirs.

    Usage docs are in docs/usage/fabfiles.rst, in "Fabfile discovery."
    """
    if os.path.dirname(state.env.fabfile):
        expanded = os.path.expanduser(state.env.fabfile)
        if os.path.exists(expanded):
            return os.path.abspath(expanded)
        else:
            return None
    else:
        path = '.'
        # Stop before falling off root of filesystem (should be platform
        # agnostic)
        while os.path.split(os.path.abspath(path))[1]:
            joined = os.path.join(path, state.env.fabfile)
            if os.path.exists(joined):
                return os.path.abspath(joined)
            path = os.path.join('..', path)
        return None


def is_task(tup):
    """
    Takes (name, object) tuple, returns True if it's a non-Fab public callable.
    """
    name, func = tup
    return (
        callable(func)
        and (func not in _internals)
        and not name.startswith('_')
    )


def load_fabfile(path):
    """
    Import given fabfile path and return (docstring, callables).

    Specifically, the fabfile's ``__doc__`` attribute (a string) and a
    dictionary of ``{'name': callable}`` containing all callables which pass
    the "is a Fabric task" test.
    """
    # Get directory and fabfile name
    directory, fabfile = os.path.split(path)
    # If the directory isn't in the PYTHONPATH, add it so our import will work
    added_to_path = False
    index = None
    if directory not in sys.path:
        sys.path.insert(0, directory)
        added_to_path = True
    # If the directory IS in the PYTHONPATH, move it to the front temporarily,
    # otherwise other fabfiles -- like Fabric's own -- may scoop the intended
    # one.
    else:
        i = sys.path.index(directory)
        if i != 0:
            # Store index for later restoration
            index = i
            # Add to front, then remove from original position
            sys.path.insert(0, directory)
            del sys.path[i + 1]
    # Perform the import (trimming off the .py)
    imported = __import__(os.path.splitext(fabfile)[0])
    # Remove directory from path if we added it ourselves (just to be neat)
    if added_to_path:
        del sys.path[0]
    # Put back in original index if we moved it
    if index is not None:
        sys.path.insert(index + 1, directory)
        del sys.path[0]
    # Return our two-tuple
    tasks = dict(filter(is_task, vars(imported).items()))
    return imported.__doc__, tasks


def parse_options():
    """
    Handle command-line options with optparse.OptionParser.

    Return list of arguments, largely for use in `parse_arguments`.
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

    # Display info about a specific command
    parser.add_option('-d', '--display',
        metavar='COMMAND',
        help="print detailed info about a given command and exit"
    )

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


def list_commands(docstring):
    """
    Print all found commands/tasks, then exit. Invoked with ``-l/--list.``

    If ``docstring`` is non-empty, it will be printed before the task list.
    """
    if docstring:
        trailer = "\n" if not docstring.endswith("\n") else ""
        print(docstring + trailer)
    print("Available commands:\n")
    # Want separator between name, description to be straight col
    max_len = reduce(lambda a, b: max(a, len(b)), commands.keys(), 0)
    sep = '  '
    trail = '...'
    names = sorted(commands.keys())
    for name in names:
        output = None
        # Print first line of docstring
        func = commands[name]
        if func.__doc__:
            lines = filter(None, func.__doc__.splitlines())
            first_line = lines[0].strip()
            # Truncate it if it's longer than N chars
            size = 75 - (max_len + len(sep) + len(trail))
            if len(first_line) > size:
                first_line = first_line[:size] + trail
            output = name.ljust(max_len) + sep + first_line
        # Or nothing (so just the name)
        else:
            output = name
        print(indent(output))
    sys.exit(0)


def display_command(command):
    """
    Print command function's docstring, then exit. Invoked with -d/--display.
    """
    # Sanity check
    if command not in commands:
        abort("Command '%s' not found, exiting." % command)
    cmd = commands[command]
    # Print out nicely presented docstring if found
    if cmd.__doc__:
        print("Displaying detailed information for command '%s':" % command)
        print('')
        print(indent(cmd.__doc__, strip=True))
        print('')
    # Or print notice if not
    else:
        print("No detailed information available for command '%s':" % command)
    sys.exit(0)


def parse_arguments(arguments):
    """
    Parse string list into list of tuples: command, args, kwargs, hosts, roles.

    See docs/usage/fab.rst, section on "per-task arguments" for details.
    """
    cmds = []
    for cmd in arguments:
        args = []
        kwargs = {}
        hosts = []
        roles = []
        if ':' in cmd:
            cmd, argstr = cmd.split(':', 1)
            for pair in argstr.split(','):
                k, _, v = pair.partition('=')
                if v:
                    # Catch, interpret host/hosts/role/roles kwargs
                    if k in ['host', 'hosts', 'role', 'roles']:
                        if k == 'host':
                            hosts = [v.strip()]
                        elif k == 'hosts':
                            hosts = [x.strip() for x in v.split(';')]
                        elif k == 'role':
                            roles = [v.strip()]
                        elif k == 'roles':
                            roles = [x.strip() for x in v.split(';')]
                    # Otherwise, record as usual
                    else:
                        kwargs[k] = v
                else:
                    args.append(k)
        cmds.append((cmd, args, kwargs, hosts, roles))
    return cmds


def _merge(hosts, roles):
    """
    Merge given host and role lists into one list of deduped hosts.
    """
    # Abort if any roles don't exist
    bad_roles = [x for x in roles if x not in state.env.roledefs]
    if bad_roles:
        abort("The following specified roles do not exist:\n%s" % (
            indent(bad_roles)
        ))

    # Look up roles, turn into flat list of hosts
    role_hosts = (
        roles
        and reduce(add, [state.env.roledefs[y] for y in roles])
        or []
    )
    # Return deduped combo of hosts and role_hosts
    return list(set(hosts + role_hosts))


def get_hosts(command, cli_hosts, cli_roles):
    """
    Return the host list the given command should be using.

    See :ref:`execution-model` for detailed documentation on how host lists are
    set.
    """
    # Command line per-command takes precedence over anything else.
    if cli_hosts or cli_roles:
        return _merge(cli_hosts, cli_roles)
    # Decorator-specific hosts/roles go next
    func_hosts = getattr(command, 'hosts', [])
    func_roles = getattr(command, 'roles', [])
    if func_hosts or func_roles:
        return _merge(func_hosts, func_roles)
    # Finally, the env is checked (which might contain globally set lists from
    # the CLI or from module-level code). This will be the empty list if these
    # have not been set -- which is fine, this method should return an empty
    # list if no hosts have been set anywhere.
    return _merge(state.env['hosts'], state.env['roles'])


def update_output_levels(show, hide):
    """
    Update state.output values as per given comma-separated list of key names.

    For example, ``update_output_levels(show='debug,warnings')`` is
    functionally equivalent to ``state.output['debug'] = True ;
    state.output['warnings'] = True``. Conversely, anything given to ``hide``
    sets the values to ``False``.
    """
    if show:
        for key in show.split(','):
            state.output[key] = True
    if hide:
        for key in hide.split(','):
            state.output[key] = False


def main():
    """
    Main command-line execution loop.
    """
    try:
        # Parse command line options
        parser, options, arguments = parse_options()

        # Update env with any overridden option values
        # NOTE: This needs to remain the first thing that occurs
        # post-parsing, since so many things hinge on the values in env.
        for option in env_options:
            state.env[option.dest] = getattr(options, option.dest)

        # Handle --hosts, --roles (comma separated string => list)
        for key in ['hosts', 'roles']:
            if key in state.env and isinstance(state.env[key], str):
                state.env[key] = state.env[key].split(',')

        # Handle output control level show/hide
        update_output_levels(show=options.show, hide=options.hide)

        # Handle version number option
        if options.show_version:
            print("Fabric %s" % state.env.version)
            sys.exit(0)

        # Handle case where we were called bare, i.e. just "fab", and print
        # a help message.
        if not (options.list_commands or options.display or arguments):
            parser.print_help()
            sys.exit(1)

        # Load settings from user settings file, into shared env dict.
        state.env.update(load_settings(state.env.rcfile))

        # Find local fabfile path or abort
        fabfile = find_fabfile()
        if not fabfile:
            abort("Couldn't find any fabfiles!")

        # Store absolute path to fabfile in case anyone needs it
        state.env.real_fabfile = fabfile

        # Load fabfile (which calls its module-level code, including
        # tweaks to env values) and put its commands in the shared commands
        # dict
        docstring, callables = load_fabfile(fabfile)
        commands.update(callables)

        # Abort if no commands found
        if not commands:
            abort("Fabfile didn't contain any commands!")

        # Now that we're settled on a fabfile, inform user.
        if state.output.debug:
            print("Using fabfile '%s'" % fabfile)

        # Handle list-commands option (now that commands are loaded)
        if options.list_commands:
            list_commands(docstring)

        # Handle show (command-specific help) option
        if options.display:
            display_command(options.display)

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
            abort("Command(s) not found:\n%s" \
                % indent(unknown_commands))

        # At this point all commands must exist, so execute them in order.
        for name, args, kwargs, cli_hosts, cli_roles in commands_to_run:
            # Get callable by itself
            command = commands[name]
            # Set current command name (used for some error messages)
            state.env.command = name
            # Set host list (also copy to env)
            state.env.all_hosts = hosts = get_hosts(
                command, cli_hosts, cli_roles)
            # If hosts found, execute the function on each host in turn
            for host in hosts:
                username, hostname, port = normalize(host)
                state.env.host_string = host
                state.env.host = hostname
                # Preserve user
                prev_user = state.env.user
                state.env.user = username
                state.env.port = port
                # Actually run command
                commands[name](*args, **kwargs)
                # Put old user back
                state.env.user = prev_user
            # If no hosts found, assume local-only and run once
            if not hosts:
                commands[name](*args, **kwargs)
        # If we got here, no errors occurred, so print a final note.
        if state.output.status:
            print("\nDone.")
    except SystemExit:
        # a number of internal functions might raise this one.
        raise
    except KeyboardInterrupt:
        if state.output.status:
            print >> sys.stderr, "\nStopped."
        sys.exit(1)
    except:
        sys.excepthook(*sys.exc_info())
        # we might leave stale threads if we don't explicitly exit()
        sys.exit(1)
    finally:
        # Explicitly disconnect from all servers
        for key in connections.keys():
            if state.output.status:
                print "Disconnecting from %s..." % denormalize(key),
            connections[key].close()
            if state.output.status:
                print "done."
    sys.exit(0)
