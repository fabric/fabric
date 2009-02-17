#!/usr/bin/env python -i

# Fabric - Pythonic remote deployment tool.
# Copyright (C) 2008  Christian Vest Hansen
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


from subroutines import format, abort, warn
from state import env


def main():
    """
    Primary execution path when invoked as 'fab'. Imports first fabfile found,
    parses command line arguments, and executes commands if found.
    """
    args = sys.argv[1:]
    try:
        try:
            # Print header
            print("Fabric v. %(fab_version)s." % env)

            # Load settings from ~/.fabric
            if not win32:
                cfg = os.path.expanduser(env['fab_settings_file'])
            else:
                from win32com.shell.shell import SHGetSpecialFolderPath
                from win32com.shell.shellcon import CSIDL_PROFILE
                cfg = SHGetSpecialFolderPath(0,CSIDL_PROFILE) + "/.fabric"
            if os.path.exists(cfg):
                comments = lambda s: s and not s.startswith("#")
                settings = filter(comments, open(cfg, 'r'))
                settings = [(k.strip(), v.strip()) for k, _, v in
                    [partition(s, '=') for s in settings]]
                ENV.update(settings)

            # Figure out where the local fabfile is
            # TODO: look upwards in dir hierarchy as well, not just cwd
            guesses = ['fabfile', 'Fabfile']
            options = filter(lambda x: os.path.exists(x + '.py'), guesses)
            # Abort if none of our guesses were found
            if not options:
                _fail({'fail': 'abort'}, "Couldn't find any fabfiles!")
            # Figure out what commands+options the user wants to invoke
            commands_to_run = _parse_args(args)
            # Load user fabfile (first one found)
            # Need to add cwd to PythonPath first, though!
            sys.path.insert(0, os.getcwd())
            ALL_COMMANDS = load(options[0])
            # Load Fabric builtin commands
            # TODO: error on collision with Python keywords, builtins, or
            ALL_COMMANDS.update(load('builtins'))
            # Error if command list was empty
            if not commands_to_run:
                _fail({'fail': 'abort'}, "No commands specified!")
            # Figure out if any specified names are invalid
            unknown_commands = []
            for command in commands_to_run:
                if not command[0] in ALL_COMMANDS:
                    unknown_commands.append(command[0])
            # Error if any unknown commands were specified
            if unknown_commands:
                _fail({'fail': 'abort'}, "Command(s) not found:\n%s" % _indent(
                    unknown_commands
                ))
            # At this point all commands must exist, so execute them in order.
            for tup in commands_to_run:
                # TODO: handle call chain
                # TODO: handle requires
                ALL_COMMANDS[tup[0]](*tup[1], **tup[2])
        finally:
            _disconnect()
        print("Done.")
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
