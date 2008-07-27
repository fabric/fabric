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

import datetime
import getpass
import os
import os.path
import pwd
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import types

try:
    import paramiko as ssh
except ImportError:
    print("Error: paramiko is a required module. Please install it:")
    print("  $ sudo easy_install paramiko")
    sys.exit(1)

__version__ = '0.0.8'
__author__ = 'Christian Vest Hansen'
__author_email__ = 'karmazilla@gmail.com'
__url__ = 'http://www.nongnu.org/fab/'
__license__ = 'GPL-2'
__greeter__ = '''\
   Fabric v. %(fab_version)s, Copyright (C) 2008 %(fab_author)s.
   Fabric comes with ABSOLUTELY NO WARRANTY; for details type `fab warranty'.
   This is free software, and you are welcome to redistribute it
   under certain conditions; type `fab license' for details.
'''

ENV = {
    'fab_version': __version__,
    'fab_author': __author__,
    'fab_mode': 'broad',
    'fab_submode': 'serial',
    'fab_port': 22,
    'fab_hosts': [],
    'fab_user': pwd.getpwuid(os.getuid())[0],
    'fab_password': None,
    'fab_sudo_prompt': 'sudo password:',
    'fab_pkey': None,
    'fab_key_filename': None,
    'fab_new_host_key': 'accept',
    'fab_shell': '/bin/bash -l -c "%s"',
    'fab_timestamp': datetime.datetime.utcnow().strftime('%F_%H-%M-%S'),
    'fab_print_real_sudo': False,
    'fab_fail': 'abort',
}

CONNECTIONS = []
COMMANDS = {}
OPERATIONS = {}
_LAZY_FORMAT_SUBSTITUTER = re.compile(r'\$\((?P<var>\w+?)\)')

#
# Compatibility fixes
#
if hasattr(str, 'partition'):
    partition = str.partition
else:
    def partition(txt, sep):
        idx = txt.find(sep)
        if idx == -1:
            return txt, '', ''
        else:
            return (txt[:idx], sep, txt[idx + len(sep):])

#
# Helper decorators for use in Fabric itself:
#
def new_registering_decorator(registry):
    def registering_decorator(first_arg=None):
        if callable(first_arg):
            registry[first_arg.__name__] = first_arg
            return first_arg
        else:
            def sub_decorator(f):
                registry[first_arg] = f
                return f
            return sub_decorator
    return registering_decorator
command = new_registering_decorator(COMMANDS)
operation = new_registering_decorator(OPERATIONS)

def connects(op_fn):
    def wrapper(*args, **kwargs):
        # If broad, run per host.
        if ENV['fab_local_mode'] == 'broad':
            # If serial, run on each host in order
            if ENV['fab_submode'] == 'serial':
                return _run_serially(op_fn, *args, **kwargs)
            # If parallel, create per-host threads
            elif ENV['fab_submode'] == 'parallel':
                return _run_parallel(op_fn, *args, **kwargs)
        # If deep, no need to multiplex here, just run for the current host
        # (set farther up the stack)
        elif ENV['fab_local_mode'] == 'deep':
            # host_conn is stored in global ENV only if we're in deep mode.
            host_conn = ENV['fab_host_conn']
            env = host_conn.get_env()
            env['fab_current_operation'] = op_fn.__name__
            host = env['fab_host']
            client = host_conn.client
            return _try_run_operation(op_fn, host, client, env, *args, **kwargs)
        # Only broad/deep supported.
        else:
            print("Unsupported fab_mode: %s" % ENV['fab_local_mode'])
            print("Supported modes are 'broad' or 'deep'.")
            sys.exit(1)

    # Mark this operation as requiring a connection
    wrapper.connects = True
    # Copy over original docstring, name
    wrapper.__doc__ = op_fn.__doc__
    wrapper.__name__ = op_fn.__name__
    return wrapper


#
# Helper decorators for use in fabfiles:
#
def hosts(*hosts):
    "Tags function object with desired fab_hosts to run on."
    def decorator(fn):
        fn.hosts = hosts
        return fn
    return decorator

def mode(mode):
    "Tags function object with desired fab_mode to run in."
    def decorator(fn):
        fn.mode = mode
        return fn
    return decorator


#
# Standard fabfile operations:
#
@operation
def set(**variables):
    """
    Set a number of Fabric environment variables.
    
    set() takes a number of keyword arguments, and defines or updates the
    variables that correspond to each keyword with the respective value.
    
    The values can be of any type, but strings are used for most variables.
    If the value is a string and contain any eager variable references, such as
    %(fab_user)s, then these will be expanded to their corresponding value.
    Lazy references, those beginning with a $ rather than a %, will not be
    expanded.
    
    Example:
        set(fab_user='joe.shmoe', fab_mode='rolling')
    
    """
    for k, v in variables.items():
        if isinstance(v, types.StringTypes):
            ENV[k] = (v % ENV)
        else:
            ENV[k] = v

@operation
def get(name, otherwise=None):
    """
    Get the value of a given Fabric environment variable.
    
    If the variable isn't found, then this operation returns the
    value of the 'otherwise' parameter, which is None unless set.
    
    """
    return ENV.get(name, otherwise)

@operation
def getAny(*names):
    """
    Given a list of variable names as parameters, get the value of the first
    of these variables that is actually defined (and does not resolve to
    boolean False), or None.
    
    Example:
        getAny('hostname', 'ipv4', 'ipv6', 'ip', 'address')
    
    """
    for name in names:
        value = ENV.get(name)
        if value:
            return value
    # Implicit return value of None here if no names found.

@operation
def require(var, **kwargs):
    """
    Make sure that a certain environment variable is available.
    
    The 'var' parameter is a string that names the variable to check for.
    Two other optional kwargs are supported:
        * 'used_for' is a string that gets injected into, and then printed, as
          something like this string: "This variable is used for %s".
        * 'provided_by' is a list of strings that name commands which the user
          can run in order to satisfy the requirement.
    
    If the required variable is not found in the current environment, then the
    operation is stopped and Fabric halts.
    
    Example:
        require('project_name',
            used_for='finding the target deployment dir.',
            provided_by=['staging', 'production'],
        )
    
    """
    if var in ENV:
        return
    print(
        ("The '%(fab_cur_command)s' command requires a '" + var
        + "' variable.") % ENV
    )
    if 'used_for' in kwargs:
        print("This variable is used for %s" % _lazy_format(
            kwargs['used_for']))
    if 'provided_by' in kwargs:
        print("Get the variable by running one of these commands:")
        to_s = lambda obj: getattr(obj, '__name__', str(obj))
        provided_by = [to_s(obj) for obj in kwargs['provided_by']]
        print('\t' + ('\n\t'.join(provided_by)))
    sys.exit(1)

@operation
def prompt(varname, msg, validate=None, default=None):
    """
    Display a prompt to the user and store the input in the given variable.
    If the variable already exists, then it is not prompted for again.
    
    The 'validate' parameter is a callable that raises an exception on invalid
    inputs and returns the input for storage in ENV.
    It may process the input and convert it to a different type, as in the
    second example below.
    
    Example:
        # Simplest form:
        prompt('environment', 'Please specify target environment')
        
        # With default:
        prompt('dish', 'Specify favorite dish', default='spam & eggs')
        
        # With validation, i.e. require integer input:
        prompt('nice', 'Please specify process nice level', validate=int)
    
    """
    if varname in ENV and ENV[varname] is not None:
        return
    
    if callable(default):
        default = default()
    
    try:
        default_str = default and (" [%s]" % str(default).strip()) or ""
        prompt_msg = _lazy_format("%s%s: " % (msg.strip(), default_str))
        value = raw_input(prompt_msg)
        if not value:
            value = default
        
        if callable(validate):
            value = validate(value)
        
        set(**{varname: value})
    except EOFError:
        return

@operation
@connects
def put(host, client, env, localpath, remotepath, **kwargs):
    """
    Upload a file to the current hosts.
    
    The 'localpath' parameter is the relative or absolute path to the file on
    your localhost that you wish to upload to the fab_hosts.
    The 'remotepath' parameter is the destination path on the individual
    fab_hosts, and relative paths are relative to the fab_user's home
    directory.
    
    May take an additional 'fail' keyword argument with one of these values:
        * ignore - do nothing on failure
        * warn - print warning on failure
        * abort - terminate fabric on failure
    
    Example:
        put('bin/project.zip', '/tmp/project.zip')
    
    """
    localpath = _lazy_format(localpath, env)
    remotepath = _lazy_format(remotepath, env)
    if not os.path.exists(localpath):
        return False
    ftp = client.open_sftp()
    print("[%s] put: %s -> %s" % (host, localpath, remotepath))
    ftp.put(localpath, remotepath)
    return True

@operation
@connects
def download(host, client, env, remotepath, localpath, **kwargs):
    """
    Download a file from the remote hosts.
    
    The 'remotepath' parameter is the relative or absolute path to the files
    to download from the fab_hosts. The 'localpath' parameter will be suffixed
    with the individual hostname from which they were downloaded, and the
    downloaded files will then be stored in those respective paths.
    
    May take an additional 'fail' keyword argument with one of these values:
        * ignore - do nothing on failure
        * warn - print warning on failure
        * abort - terminate fabric on failure
    
    Example:
        set(fab_hosts=['node1.cluster.com', 'node2.cluster.com'])
        download('/var/log/server.log', 'server.log')
    
    The above code will produce two files on your local system, called
    "server.log.node1.cluster.com" and "server.log.node2.cluster.com"
    respectively.
    
    """
    ftp = client.open_sftp()
    localpath = _lazy_format(localpath) + '.' + host
    remotepath = _lazy_format(remotepath)
    print("[%s] download: %s <- %s" % (host, localpath, remotepath))
    ftp.get(remotepath, localpath)
    return True

@operation
@connects
def run(host, client, env, cmd, **kwargs):
    """
    Run a shell command on the current fab_hosts.
    
    The provided command is executed with the permissions of fab_user, and the
    exact execution environ is determined by the fab_shell variable.
    
    May take an additional 'fail' keyword argument with one of these values:
        * ignore - do nothing on failure
        * warn - print warning on failure
        * abort - terminate fabric on failure
    
    Example:
        run("ls")
    
    """
    cmd = _lazy_format(cmd, env)
    real_cmd = env['fab_shell'] % cmd.replace('"', '\\"')
    if not _confirm_proceed('run', host, kwargs):
        return False
    print("[%s] run: %s" % (host, cmd))
    chan = client._transport.open_session()
    chan.exec_command(real_cmd)
    capture = []

    out_th = _start_outputter("[%s] out" % host, chan, False, capture)
    err_th = _start_outputter("[%s] err" % host, chan, True)
    status = chan.recv_exit_status()
    chan.close()

    return ("".join(capture.strip()), status == 0)

@operation
@connects
def sudo(host, client, env, cmd, **kwargs):
    """
    Run a sudo (root privileged) command on the current hosts.
    
    The provided command is executed with root permissions, provided that
    fab_user is in the sudoers file in the remote host. The exact execution
    environ is determined by the fab_shell variable - the 'sudo' part is
    injected into this variable.
    
    May take an additional 'fail' keyword argument with one of these values:
        * ignore - do nothing on failure
        * warn - print warning on failure
        * abort - terminate fabric on failure
    
    Example:
        sudo("install_script.py")
    
    """
    cmd = _lazy_format(cmd, env)
    passwd = get('fab_password')
    real_cmd = env['fab_shell'] % (
        "sudo -S -p '%s' " % ENV['fab_sudo_prompt']
        + cmd.replace('"', '\\"')
    )
    cmd = env['fab_print_real_sudo'] and real_cmd or cmd
    if not _confirm_proceed('sudo', host, kwargs):
        return False # TODO: should we return False in fail??
    print("[%s] sudo: %s" % (host, cmd))
    chan = client._transport.open_session()
    chan.exec_command(real_cmd)
    capture = []

    out_th = _start_outputter("[%s] out" % host, chan, False, capture)
    err_th = _start_outputter("[%s] err" % host, chan, True)
    status = chan.recv_exit_status()
    chan.close()

    return ("".join(capture).strip(), status == 0)

@operation
def local(cmd, **kwargs):
    """
    Run a command locally.
    
    This operation is essentially 'os.system()' except that variables are
    expanded prior to running.
    
    May take an additional 'fail' keyword argument with one of these values:
        * ignore - do nothing on failure
        * warn - print warning on failure
        * abort - terminate fabric on failure
    
    Example:
        local("make clean dist", fail='abort')
    
    """
    final_cmd = _lazy_format(cmd)
    print("[localhost] run: " + final_cmd)
    retcode = subprocess.call(final_cmd, shell=True)
    if retcode != 0:
        _fail(kwargs, "Local command failed:\n" + _indent(final_cmd))

@operation
@connects
def local_per_host(cmd, **kwargs):
    """
    Run a command locally, for every defined host.
    
    Like the local() operation, this is pretty similar to 'os.system()', but
    with this operation, the command is executed (and have its variables
    expanded) for each host in fab_hosts.
    
    May take an additional 'fail' keyword argument with one of these values:
        * ignore - do nothing on failure
        * warn - print warning on failure
        * abort - terminate fabric on failure
    
    Example:
        local_per_host("scp -i login.key stuff.zip $(fab_host):stuff.zip")
    
    """
    for host_conn in CONNECTIONS:
        env = host_conn.get_env()
        final_cmd = _lazy_format(cmd, env)
        print(_lazy_format("[localhost/$(fab_host)] run: " + final_cmd, env))
        retcode = subprocess.call(final_cmd, shell=True)
        if retcode != 0:
            _fail(kwargs, "Local command failed:\n" + _indent(final_cmd))

@operation
def load(filename, **kwargs):
    """
    Load up the given fabfile.
    
    This loads the fabfile specified by the 'filename' parameter into fabric
    and make its commands and other functions available in the scope of the 
    current fabfile.
    
    May take an additional 'fail' keyword argument with one of these values:
        * ignore - do nothing on failure
        * warn - print warning on failure
        * abort - terminate fabric on failure
    
    Example:
        load("conf/production-settings.py")
    
    """
    if os.path.exists(filename):
        execfile(filename)
        for name, obj in locals().items():
            if not name.startswith('_') and isinstance(obj, types.FunctionType):
                COMMANDS[name] = obj
            if not name.startswith('_'):
                __builtins__[name] = obj
    else:
        _fail(kwargs, "Load failed:\n" + _indent(
            "File not found: " + filename))

@operation
def upload_project(**kwargs):
    """
    Uploads the current project directory to the connected hosts.
    
    This is a higher-level convenience operation that basically 'tar' up the
    directory that contains your fabfile (presumably it is your project
    directory), uploads it to the fab_hosts and 'untar' it.
    
    This operation expects the tar command-line utility to be available on your
    local machine, and it also expects your system to have a /tmp directory
    that is writeable.
    
    Unless something fails half-way through, this operation will make sure to
    delete the temporary files it creates.
    
    """
    tar_file = "/tmp/fab.%(fab_timestamp)s.tar" % ENV
    cwd_name = os.getcwd().split(os.sep)[-1]
    local("tar -czf %s ." % tar_file, **kwargs)
    put(tar_file, cwd_name + ".tar.gz", **kwargs)
    local("rm -f " + tar_file, **kwargs)
    run("tar -xzf " + cwd_name, **kwargs)
    run("rm -f " + cwd_name + ".tar.gz", **kwargs)

@operation
def abort(msg):
    "Simple way for users to have their commands abort the process."
    print(_lazy_format('[$(fab_host)] Error: %s' % msg, ENV))
    sys.exit(1)

#
# Standard Fabric commands:
#
@mode("broad")
@command("help")
def _help(**kwargs):
    """
    Display Fabric usage help, or help for a given command.
    
    You can provide help with a parameter and get more detailed help for a
    specific command. For instance, to learn more about the list command, you
    could run 'fab help:list'.
    
    If you are developing your own fabfile, then you might also be interested
    in learning more about operations. You can do this by running help with the
    'op' parameter set to the name of the operation you would like to learn
    more about. For instance, to learn more about the 'run' operation, you
    could run 'fab help:op=run'.
    
    """
    if kwargs:
        for k, v in kwargs.items():
            if k in COMMANDS:
                _print_help_for_in(k, COMMANDS)
            elif k in OPERATIONS:
                _print_help_for_in(k, OPERATIONS)
            elif k in ['op', 'operation']:
                _print_help_for_in(kwargs[k], OPERATIONS)
            else:
                _print_help_for(k, None)
    else:
        print("""
    Fabric is a simple pythonic remote deployment tool.
    
    Type 'fab list' to get a list of available commands.
    Type 'fab help:help' to get more information on how to use the built in
    help.
    
    """)

@mode("broad")
@command("list")
def _list_commands(**kwargs):
    """
    Display a list of commands with descriptions.
    
    By default, the list command prints a list of available commands, with a
    short description (if one is available). However, the list command can also
    print a list of available operations if you provide it with the 'ops' or
    'operations' parameters.
    
    """
    if kwargs:
        for k, v in kwargs.items():
            if k in ['cmds', 'commands']:
                print("Available commands are:")
                _list_objs(COMMANDS)
            elif k in ['ops', 'operations']:
                print("Available operations are:")
                _list_objs(OPERATIONS)
            else:
                print("Don't know how to list '%s'." % k)
                print("Try one of these instead:")
                print(_indent('\n'.join([
                    'cmds', 'commands',
                    'ops', 'operations',
                ])))
                sys.exit(1)
    else:
        print("Available commands are:")
        _list_objs(COMMANDS)

@mode("broad")
@command("license")
def _license():
    "Display the Fabric distribution license text."
    print("""		    GNU GENERAL PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. This License applies to any program or other work which contains
a notice placed by the copyright holder saying it may be distributed
under the terms of this General Public License.  The "Program", below,
refers to any such program or work, and a "work based on the Program"
means either the Program or any derivative work under copyright law:
that is to say, a work containing the Program or a portion of it,
either verbatim or with modifications and/or translated into another
language.  (Hereinafter, translation is included without limitation in
the term "modification".)  Each licensee is addressed as "you".

Activities other than copying, distribution and modification are not
covered by this License; they are outside its scope.  The act of
running the Program is not restricted, and the output from the Program
is covered only if its contents constitute a work based on the
Program (independent of having been made by running the Program).
Whether that is true depends on what the Program does.

  1. You may copy and distribute verbatim copies of the Program's
source code as you receive it, in any medium, provided that you
conspicuously and appropriately publish on each copy an appropriate
copyright notice and disclaimer of warranty; keep intact all the
notices that refer to this License and to the absence of any warranty;
and give any other recipients of the Program a copy of this License
along with the Program.

You may charge a fee for the physical act of transferring a copy, and
you may at your option offer warranty protection in exchange for a fee.

  2. You may modify your copy or copies of the Program or any portion
of it, thus forming a work based on the Program, and copy and
distribute such modifications or work under the terms of Section 1
above, provided that you also meet all of these conditions:

    a) You must cause the modified files to carry prominent notices
    stating that you changed the files and the date of any change.

    b) You must cause any work that you distribute or publish, that in
    whole or in part contains or is derived from the Program or any
    part thereof, to be licensed as a whole at no charge to all third
    parties under the terms of this License.

    c) If the modified program normally reads commands interactively
    when run, you must cause it, when started running for such
    interactive use in the most ordinary way, to print or display an
    announcement including an appropriate copyright notice and a
    notice that there is no warranty (or else, saying that you provide
    a warranty) and that users may redistribute the program under
    these conditions, and telling the user how to view a copy of this
    License.  (Exception: if the Program itself is interactive but
    does not normally print such an announcement, your work based on
    the Program is not required to print an announcement.)

These requirements apply to the modified work as a whole.  If
identifiable sections of that work are not derived from the Program,
and can be reasonably considered independent and separate works in
themselves, then this License, and its terms, do not apply to those
sections when you distribute them as separate works.  But when you
distribute the same sections as part of a whole which is a work based
on the Program, the distribution of the whole must be on the terms of
this License, whose permissions for other licensees extend to the
entire whole, and thus to each and every part regardless of who wrote it.

Thus, it is not the intent of this section to claim rights or contest
your rights to work written entirely by you; rather, the intent is to
exercise the right to control the distribution of derivative or
collective works based on the Program.

In addition, mere aggregation of another work not based on the Program
with the Program (or with a work based on the Program) on a volume of
a storage or distribution medium does not bring the other work under
the scope of this License.

  3. You may copy and distribute the Program (or a work based on it,
under Section 2) in object code or executable form under the terms of
Sections 1 and 2 above provided that you also do one of the following:

    a) Accompany it with the complete corresponding machine-readable
    source code, which must be distributed under the terms of Sections
    1 and 2 above on a medium customarily used for software interchange; or,

    b) Accompany it with a written offer, valid for at least three
    years, to give any third party, for a charge no more than your
    cost of physically performing source distribution, a complete
    machine-readable copy of the corresponding source code, to be
    distributed under the terms of Sections 1 and 2 above on a medium
    customarily used for software interchange; or,

    c) Accompany it with the information you received as to the offer
    to distribute corresponding source code.  (This alternative is
    allowed only for noncommercial distribution and only if you
    received the program in object code or executable form with such
    an offer, in accord with Subsection b above.)

The source code for a work means the preferred form of the work for
making modifications to it.  For an executable work, complete source
code means all the source code for all modules it contains, plus any
associated interface definition files, plus the scripts used to
control compilation and installation of the executable.  However, as a
special exception, the source code distributed need not include
anything that is normally distributed (in either source or binary
form) with the major components (compiler, kernel, and so on) of the
operating system on which the executable runs, unless that component
itself accompanies the executable.

If distribution of executable or object code is made by offering
access to copy from a designated place, then offering equivalent
access to copy the source code from the same place counts as
distribution of the source code, even though third parties are not
compelled to copy the source along with the object code.

  4. You may not copy, modify, sublicense, or distribute the Program
except as expressly provided under this License.  Any attempt
otherwise to copy, modify, sublicense or distribute the Program is
void, and will automatically terminate your rights under this License.
However, parties who have received copies, or rights, from you under
this License will not have their licenses terminated so long as such
parties remain in full compliance.

  5. You are not required to accept this License, since you have not
signed it.  However, nothing else grants you permission to modify or
distribute the Program or its derivative works.  These actions are
prohibited by law if you do not accept this License.  Therefore, by
modifying or distributing the Program (or any work based on the
Program), you indicate your acceptance of this License to do so, and
all its terms and conditions for copying, distributing or modifying
the Program or works based on it.

  6. Each time you redistribute the Program (or any work based on the
Program), the recipient automatically receives a license from the
original licensor to copy, distribute or modify the Program subject to
these terms and conditions.  You may not impose any further
restrictions on the recipients' exercise of the rights granted herein.
You are not responsible for enforcing compliance by third parties to
this License.

  7. If, as a consequence of a court judgment or allegation of patent
infringement or for any other reason (not limited to patent issues),
conditions are imposed on you (whether by court order, agreement or
otherwise) that contradict the conditions of this License, they do not
excuse you from the conditions of this License.  If you cannot
distribute so as to satisfy simultaneously your obligations under this
License and any other pertinent obligations, then as a consequence you
may not distribute the Program at all.  For example, if a patent
license would not permit royalty-free redistribution of the Program by
all those who receive copies directly or indirectly through you, then
the only way you could satisfy both it and this License would be to
refrain entirely from distribution of the Program.

If any portion of this section is held invalid or unenforceable under
any particular circumstance, the balance of the section is intended to
apply and the section as a whole is intended to apply in other
circumstances.

It is not the purpose of this section to induce you to infringe any
patents or other property right claims or to contest validity of any
such claims; this section has the sole purpose of protecting the
integrity of the free software distribution system, which is
implemented by public license practices.  Many people have made
generous contributions to the wide range of software distributed
through that system in reliance on consistent application of that
system; it is up to the author/donor to decide if he or she is willing
to distribute software through any other system and a licensee cannot
impose that choice.

This section is intended to make thoroughly clear what is believed to
be a consequence of the rest of this License.

  8. If the distribution and/or use of the Program is restricted in
certain countries either by patents or by copyrighted interfaces, the
original copyright holder who places the Program under this License
may add an explicit geographical distribution limitation excluding
those countries, so that distribution is permitted only in or among
countries not thus excluded.  In such case, this License incorporates
the limitation as if written in the body of this License.

  9. The Free Software Foundation may publish revised and/or new versions
of the General Public License from time to time.  Such new versions will
be similar in spirit to the present version, but may differ in detail to
address new problems or concerns.

Each version is given a distinguishing version number.  If the Program
specifies a version number of this License which applies to it and "any
later version", you have the option of following the terms and conditions
either of that version or of any later version published by the Free
Software Foundation.  If the Program does not specify a version number of
this License, you may choose any version ever published by the Free Software
Foundation.

  10. If you wish to incorporate parts of the Program into other free
programs whose distribution conditions are different, write to the author
to ask for permission.  For software which is copyrighted by the Free
Software Foundation, write to the Free Software Foundation; we sometimes
make exceptions for this.  Our decision will be guided by the two goals
of preserving the free status of all derivatives of our free software and
of promoting the sharing and reuse of software generally.""")

@mode("broad")
@command("warranty")
def _warranty():
    "Display warranty information for the Fabric software."
    print("""			    NO WARRANTY

  BECAUSE THE PROGRAM IS LICENSED FREE OF CHARGE, THERE IS NO WARRANTY
FOR THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW.  EXCEPT WHEN
OTHERWISE STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES
PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED
OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.  THE ENTIRE RISK AS
TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU.  SHOULD THE
PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING,
REPAIR OR CORRECTION.

  IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR
REDISTRIBUTE THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES,
INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING
OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED
TO LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY
YOU OR THIRD PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER
PROGRAMS), EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE
POSSIBILITY OF SUCH DAMAGES.""")

@mode("broad")
@command("set")
def _set(**kwargs):
    """
    Set a Fabric variable.
    
    Example:
        $fab set:fab_user=billy,other_var=other_value
    """
    for k, v in kwargs.items():
        ENV[k] = (v % ENV)

@mode("broad")
@command("shell")
def _shell(**kwargs):
    """
    Start an interactive shell connection to the specified hosts.
    
    Optionally takes a list of hostnames as arguments, if Fabric is, by
    the time this command runs, not already connected to one or more
    hosts. If you provide hostnames and Fabric is already connected, then
    Fabric will, depending on fab_fail, complain and abort.
    
    The fab_fail variable can be overwritten with the 'set' command, or
    by specifying an additional 'fail' argument.
    
    Examples:
        $fab shell
        $fab shell:localhost,127.0.0.1
        $fab shell:localhost,127.0.0.1,fail=warn
    
    """
    # expect every arg w/o a value to be a hostname
    hosts = filter(lambda k: not kwargs[k], kwargs.keys())
    if hosts:
        if CONNECTIONS:
            _fail(kwargs, "Already connected to predefined fab_hosts.")
        set(fab_hosts = hosts)
    def lines():
        try:
            while True:
                yield raw_input("fab> ")
        except EOFError:
            # user pressed ctrl-d
            print
    for line in lines():
        if line == 'exit':
            break
        elif line.startswith('sudo '):
            sudo(line[5:])
        else:
            run(line)

#
# Per-operation execution strategies for "broad" mode.
#
def _run_parallel(fn, *args, **kwargs):
    """
    A strategy that executes on all hosts in parallel.
    
    THIS STRATEGY IS CURRENTLY BROKEN!
    
    """
    err_msg = "The $(fab_current_operation) operation failed on $(fab_host)"
    threads = []
    for host_conn in CONNECTIONS:
        env = host_conn.get_env()
        env['fab_current_operation'] = fn.__name__
        host = env['fab_host']
        client = host_conn.client
        def functor():
            _try_run_operation(fn, host, client, env, *args, **kwargs)
        thread = threading.Thread(None, functor)
        thread.setDaemon(True)
        threads.append(thread)
    map(threading.Thread.start, threads)
    map(threading.Thread.join, threads)

def _run_serially(fn, *args, **kwargs):
    """One-at-a-time fail-fast strategy."""
    err_msg = "The $(fab_current_operation) operation failed on $(fab_host)"
    # Capture the first output in case someone really wants captured output
    # while running in broad mode.
    result = None
    for host_conn in CONNECTIONS:
        env = host_conn.get_env()
        env['fab_current_operation'] = fn.__name__
        host = env['fab_host']
        client = host_conn.client
        res = _try_run_operation(fn, host, client, env, *args, **kwargs)
        if not result:
            result = res
    return result

#
# Internal plumbing:
#

class HostConnection(object):
    """
    A connection to an SSH host - wraps an SSHClient.
    
    Instances of this class populate the CONNECTIONS list.
    """
    def __init__(self, hostname, port, global_env, user_local_env):
        self.global_env = global_env
        self.user_local_env = user_local_env
        self.host_local_env = {
            'fab_host': hostname,
            'fab_port': port,
        }
        self.client = None
    def get_env(self):
        "Create a new environment that is the union of local and global envs."
        env = dict(self.global_env)
        env.update(self.user_local_env)
        env.update(self.host_local_env)
        return env
    def connect(self):
        env = self.get_env()
        new_host_key = env['fab_new_host_key']
        client = ssh.SSHClient()
        client.load_system_host_keys()
        if new_host_key == 'accept':
            client.set_missing_host_key_policy(ssh.AutoAddPolicy())
        try:
            self._do_connect(client, env)
        except (ssh.AuthenticationException, ssh.SSHException):
            PASS_PROMPT = \
                "Password for $(fab_user)@$(fab_host)$(fab_passprompt_suffix)"
            if 'fab_password' in env and env['fab_password']:
                env['fab_passprompt_suffix'] = " [Enter for previous]: "
            else:
                env['fab_passprompt_suffix'] = ": "
            connected = False
            password = None
            while not connected:
                try:
                    password = getpass.getpass(_lazy_format(PASS_PROMPT, env))
                    env['fab_password'] = password
                    self._do_connect(client, env)
                    connected = True
                except ssh.AuthenticationException:
                    print("Bad password.")
                    env['fab_passprompt_suffix'] = ": "
                except (EOFError, TypeError):
                    # ctrl-D or ctrl-C on password prompt
                    print
                    sys.exit(0)
            self.host_local_env['fab_password'] = password
            self.user_local_env['fab_password'] = password
        self.client = client
    def disconnect(self):
        if self.client:
            self.client.close()
    def _do_connect(self, client, env):
        host = env['fab_host']
        port = env['fab_port']
        username = env['fab_user']
        password = env['fab_password']
        pkey = env['fab_pkey']
        key_filename = env['fab_key_filename']
        try:
            client.connect(host, port, username, password, pkey, key_filename,
                timeout=10)
        except socket.timeout:
            print('Error: timed out trying to connect to %s' % host)
            sys.exit(1)
        except socket.gaierror:
            print('Error: name lookup failed for %s' % host)
            sys.exit(1)
    def __str__(self):
        return self.host_local_env['fab_host']

def _indent(text, level=4):
    "Indent all lines in text with 'level' number of spaces, default 4."
    return '\n'.join(((' ' * level) + line for line in text.splitlines()))

def _print_help_for(name, doc):
    "Output a pretty-printed help text for the given name & doc"
    default_help_msg = '* No help-text found.'
    msg = doc or default_help_msg
    lines = msg.splitlines()
    # remove leading blank lines
    while lines and lines[0].strip() == '':
        lines = lines[1:]
    # remove trailing blank lines
    while lines and lines[-1].strip() == '':
        lines = lines[:-1]
    if lines:
        msg = '\n'.join(lines)
        if not msg.startswith('    '):
            msg = _indent(msg)
        print("Help for '%s':\n%s" % (name, msg))
    else:
        print("No help message found for '%s'." % name)

def _print_help_for_in(name, dictionary):
    "Print a pretty help text for the named function in the dict."
    if name in dictionary:
        _print_help_for(name, dictionary[name].__doc__)
    else:
        _print_help_for(name, None)

def _list_objs(objs):
    max_name_len = reduce(lambda a, b: max(a, len(b)), objs.keys(), 0)
    cmds = objs.items()
    cmds.sort(lambda x, y: cmp(x[0], y[0]))
    for name, fn in cmds:
        print '  ', name.ljust(max_name_len),
        if fn.__doc__:
            print ':', filter(None, fn.__doc__.splitlines())[0].strip()
        else:
            print

def _check_fab_hosts():
    "Check that we have a fab_hosts variable, and prompt if it's missing."
    if not ENV.get('fab_local_hosts'):
        prompt('fab_input_hosts', 'Please specify host or hosts to connect to (comma-separated)')
        hosts = ENV['fab_input_hosts']
        hosts = [x.strip() for x in hosts.split(',')]
        ENV['fab_local_hosts'] = hosts
    
def _connect():
    """Populate CONNECTIONS with HostConnection instances as per current
    fab_local_hosts."""
    signal.signal(signal.SIGINT, lambda: _disconnect() and sys.exit(0))
    global CONNECTIONS
    def_port = ENV['fab_port']
    username = ENV['fab_user']
    fab_hosts = ENV['fab_local_hosts']
    user_envs = {}
    host_connections_by_user = {}
    
    # grok fab_hosts into who connects to where
    for host in fab_hosts:
        if '@' in host:
            user, _, host_and_port = partition(host, '@')
        else:
            user, host_and_port = None, host
        hostname, _, port = partition(host_and_port, ':')
        user = user or username
        port = int(port or def_port)
        if user is not '' and user not in user_envs:
            user_envs[user] = {'fab_user': user}
        conn = HostConnection(hostname, port, ENV, user_envs[user])
        if user not in host_connections_by_user:
            host_connections_by_user[user] = [conn]
        else:
            host_connections_by_user[user].append(conn)
    
    # Print and establish connections
    for user, host_connections in host_connections_by_user.iteritems():
        user_env = dict(ENV)
        user_env.update(user_envs[user])
        print(_lazy_format("Logging into the following hosts as $(fab_user):",
            user_env))
        for conn in host_connections:
            print(_indent(str(conn)))
            conn.connect()
        CONNECTIONS += host_connections

def _disconnect():
    "Disconnect all clients."
    global CONNECTIONS
    map(HostConnection.disconnect, CONNECTIONS)
    CONNECTIONS = []

def _lazy_format(string, env=ENV):
    "Do recursive string substitution of ENV vars - both lazy and eager."
    if string is None:
        return None
    env = dict([(k, str(v)) for k, v in env.items()])
    def replacer_fn(match):
        var = match.group('var')
        if var in env:
            return _lazy_format(env[var] % env, env)
        else:
            return match.group(0)
    return re.sub(_LAZY_FORMAT_SUBSTITUTER, replacer_fn, string % env)


def _try_run_operation(fn, host, client, env, *args, **kwargs):
    """
    Used to attempt the execution of an operation, and handle any failures 
    appropriately.
    """
    err_msg = "The $(fab_current_operation) operation failed on $(fab_host)"
    result = False
    try:
        result = fn(host, client, env, *args, **kwargs)
    except SystemExit:
        raise
    except BaseException, e:
        _fail(kwargs, err_msg + ':\n' + _indent(str(e)), env)
    # Check for split output + return code (tuple)
    if isinstance(result, tuple):
        output, success = result
    # If not a tuple, assume just a pass/fail boolean.
    else:
        output = ""
        success = result
    if not success:
        _fail(kwargs, err_msg + '.', env)
    # Return any captured output (will execute if fail != abort)
    return output

def _confirm_proceed(exec_type, host, kwargs):
    if 'confirm' in kwargs:
        infotuple = (exec_type, host, _lazy_format(kwargs['confirm']))
        question = "Confirm %s for host %s: %s [yN] " % infotuple
        answer = raw_input(question)
        return answer and answer in 'yY'
    return True

def _fail(kwargs, msg, env=ENV):
    # Get failure code
    codes = {
        'ignore': (1, ''),
        'warn': (2, 'Warning: '),
        'abort': (3, 'Error: '),
    }
    code, msg_prefix = codes[env['fab_fail']]
    if 'fail' in kwargs:
        code, msg_prefix = codes[kwargs['fail']]
    # If warn or above, print message
    if code > 1:
        print(msg_prefix + _lazy_format(msg, env))
        # If abort, also exit
        if code > 2:
            sys.exit(1)


def _start_outputter(prefix, chan, is_stderr=False, capture=None):
    def outputter(prefix, chan, is_stderr, capture):
        # Read one "packet" at a time, which lets us get less-than-a-line
        # chunks of text, such as sudo prompts. However, we still print
        # them to the user one line at a time. (We also eat sudo prompts.)
        leftovers = ""
        while not chan.exit_status_ready():
            out = None
            if not is_stderr:
                if chan.recv_ready():
                    out = chan.recv(65535)
            else:
                if chan.recv_stderr_ready():
                    out = chan.recv_stderr(65535)
            if out is not None:
                # Capture if necessary
                if capture is not None:
                    capture += out
                # Handle any password prompts
                if re.findall(r'^%s:$' % ENV['fab_sudo_prompt'], out,
                    re.I|re.M):
                    chan.sendall(ENV['fab_password']+'\n')
                    out = ""
                # Deal with line breaks, printing all lines and storing the
                # leftovers, if any.
                if '\n' in out:
                    parts = out.split('\n')
                    line = leftovers + parts.pop(0)
                    leftovers = parts.pop()
                    while line:
                        sys.stdout.write("%s: %s\n" % (prefix, line)),
                        sys.stdout.flush()
                        if parts:
                            line = parts.pop(0)
                        else:
                            line = ""
                # If no line breaks, just keep adding to leftovers
                else:
                    leftovers += out
    thread = threading.Thread(None, outputter, prefix,
        (prefix, chan, is_stderr, capture))
    thread.setDaemon(True)
    thread.start()
    return thread

def _pick_fabfile():
    "Figure out what the fabfile is called."
    guesses = ['fabfile', 'Fabfile', 'fabfile.py', 'Fabfile.py']
    options = filter(os.path.exists, guesses)
    if options:
        return options[0]
    else:
        return guesses[0] # load() will barf for us...

def _load_default_settings():
    "Load user-default fabric settings from ~/.fabric"
    # TODO: http://mail.python.org/pipermail/python-list/2006-July/393819.html
    cfg = os.path.expanduser("~/.fabric")
    if os.path.exists(cfg):
        comments = lambda s: s and not s.startswith("#")
        settings = filter(comments, open(cfg, 'r'))
        settings = [(k.strip(), v.strip()) for k, _, v in
            [partition(s, '=') for s in settings]]
        ENV.update(settings)

def _parse_args(args):
    cmds = []
    for cmd in args:
        cmd_args = {}
        if ':' in cmd:
            cmd, cmd_str_args = cmd.split(':', 1)
            for cmd_arg_kv in cmd_str_args.split(','):
                k, _, v = partition(cmd_arg_kv, '=')
                cmd_args[k] = (v % ENV)
        cmds.append((cmd, cmd_args))
    return cmds

def _validate_commands(cmds):
    if not cmds:
        print("No commands given.")
        _list_commands()
    else:
        for cmd in cmds:
            if not cmd[0] in COMMANDS:
                print("No such command: %s" % cmd[0])
                sys.exit(1)

def _execute_commands(cmds):
    for cmd, args in cmds:
        # Setup
        ENV['fab_cur_command'] = cmd
        print("Running %s..." % cmd)
        if args is not None:
            args = dict(zip(args.keys(), map(_lazy_format, args.values())))
        command = COMMANDS[cmd]
        ENV['fab_local_mode'] = getattr(command, 'mode', ENV['fab_mode'])
        ENV['fab_local_hosts'] = getattr(command, 'hosts', ENV['fab_hosts'])
        # Determine whether we need to connect for this command, do so if so
        for operation in command.func_code.co_names:
            if getattr(OPERATIONS.get(operation), 'connects', False):
                _check_fab_hosts()
                _connect()
                break
        # Run command once, with each operation running once per host.
        if ENV['fab_local_mode'] == 'broad':
            command(**(args or {}))
        # Run entire command once per host.
        elif ENV['fab_local_mode'] == 'deep':
            # Gracefully handle local-only commands
            if CONNECTIONS:
                for host_conn in CONNECTIONS:
                    ENV['fab_host_conn'] = host_conn
                    ENV['fab_host'] = host_conn.host_local_env['fab_host']
                    command(**(args or {}))
            else:
                command(**(args or {}))
        # Disconnect (to clear things up for next command)
        # TODO: be intelligent, persist connections for hosts
        # that will be used again this session.
        _disconnect()


def main():
    args = sys.argv[1:]
    try:
        try:
            print(__greeter__ % ENV)
            _load_default_settings()
            fabfile = _pick_fabfile()
            load(fabfile, fail='warn')
            commands = _parse_args(args)
            _validate_commands(commands)
            _execute_commands(commands)
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
    

