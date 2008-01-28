#!/usr/bin/env python

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

import getpass
import os
import os.path
import re
import signal
import subprocess
import sys
import threading
import time
import types
import datetime

import_error = False
try:
    import paramiko as ssh
except ImportError:
    print("Error: paramiko is a required module. Please install it:")
    print("  $ sudo easy_install paramiko")
    import_error = True
try:
    from decorator import decorator
except ImportError:
    print("Error: decorator is a required module. Please install it:")
    print("  $ sudo easy_install decorator")
    import_error = True
if import_error:
    exit(1)

__version__ = '0.0.2'
__author__ = 'Christian Vest Hansen'
__author_email__ = 'karmazilla@gmail.com'
__url__ = 'https://savannah.nongnu.org/projects/fab/'
__license__ = 'GPL-2'
__greeter__ = '''\
   Fabric v. %(fab_version)s, Copyright (C) 2008 %(fab_author)s.
   Fabric comes with ABSOLUTELY NO WARRANTY; for details type `fab warranty'.
   This is free software, and you are welcome to redistribute it
   under certain conditions; type `fab license' for details.
'''

ENV = {
    'fab_version':__version__,
    'fab_author':__author__,
    'fab_mode':'fanout',
    'fab_port':22,
    'fab_user':None,
    'fab_pkey':None,
    'fab_key_filename':None,
    'fab_new_host_key':'accept',
    'fab_shell':'/bin/bash -l -c "%s"',
    # TODO: make fab_timestamp UTC
    'fab_timestamp':datetime.datetime.now().strftime('%F_%H-%M-%S'),
    'fab_debug':False,
}
COMMANDS = {}
CONNECTIONS = []
OPERATIONS = {}
_LAZY_FORMAT_SUBSTITUTER = re.compile(r'\$\((?P<var>\w+?)\)')

#
# Helper decorators
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


#
# Standard fabfile operations:
#
@operation
def set(**variables):
    """Set a number of Fabric environment variables.
    
    Set takes a number of keyword arguments, and defines or updates the
    variables that corrosponds to each keyword with the respective value.
    
    The values can be of any type, but strings are used for most variables.
    If the value is a string and contain any eager variable references, such as
    %(fab_user)s, then these will be expanded to their corrosponding value.
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
def get(name):
    """Get the value of a given Fabric environment variable.
    
    If the variable isn't found, then this operation returns None.
    
    """
    return name in ENV and ENV[name] or None

@operation
def require(var, **kvargs):
    """Make sure that a certain environmet variable is available.
    
    The 'var' parameter is a string that names the variable to check for.
    Two other optional kvargs are supported:
     - 'used_for' is a string that gets injected into, and then printed, as
       something like this string: "This variable is used for %s".
     - 'provided_by' is a list of strings that name commands which the user
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
    if 'used_for' in kvargs:
        print("This variable is used for %s" % kvargs['used_for'])
    if 'provided_by' in kvargs:
        print("Get the variable by running one of these commands:")
        print('\t' + ('\n\t'.join(kvargs['provided_by'])))
    exit(1)

@operation
def put(localpath, remotepath, **kvargs):
    """Upload a file to the current hosts.
    
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
    if not CONNECTIONS:
        _connect()
    _on_hosts_do(_put, localpath, remotepath, **kvargs)

@operation
def download(remotepath, localpath, **kvargs):
    """Download a file from the remote hosts.
    
    The 'remotepath' parameter is the relative or absolute path to the files
    to download from the fab_hosts. The 'localpath' parameter will be suffixed
    with the individual hostname from which they were downloaded, and the
    downloaded files will then be stored in those respective paths.
    
    May take an additional 'fail' keyword argument with one of these values:
        * ignore - do nothing on failure
        * warn - print warning on failure
        * abort - terminate fabric on failure
    
    Example:
        set(fab_hosts=['node1.cluster.com','node2.cluster.com'])
        download('/var/log/server.log', 'server.log')
    
    The above code will produce two files on your local system, called
    "server.log.node1.cluster.com" and "server.log.node2.cluster.com"
    respectively.
    
    """
    if not CONNECTIONS:
        _connect()
    _on_hosts_do(_download, remotepath, localpath, **kvargs)

@operation
def run(cmd, **kvargs):
    """Run a shell command on the current fab_hosts.
    
    The provided command is executed with the permisions of fab_user, and the
    exact execution environ is determined by the fab_shell variable.
    
    May take an additional 'fail' keyword argument with one of these values:
        * ignore - do nothing on failure
        * warn - print warning on failure
        * abort - terminate fabric on failure
    
    Example:
        run("ls")
    
    """
    if not CONNECTIONS:
        _connect()
    _on_hosts_do(_run, cmd, **kvargs)

@operation
def sudo(cmd, **kvargs):
    """Run a sudo (root privileged) command on the current hosts.
    
    The provided command is executed with root permisions, provided that
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
    if not CONNECTIONS:
        _connect()
    _on_hosts_do(_sudo, cmd, **kvargs)

@operation
def local(cmd, **kvargs):
    """Run a command locally.
    
    This operation is essentially 'os.system()' except that variables are
    expanded prior to running.
    
    May take an additional 'fail' keyword argument with one of these values:
        * ignore - do nothing on failure
        * warn - print warning on failure
        * abort - terminate fabric on failure
    
    Example:
        local("make clean dist")
    
    """
    final_cmd = _lazy_format(cmd)
    retcode = subprocess.call(final_cmd, shell=True)
    if retcode != 0:
        failcode = _get_failcode(kvargs)
        if failcode > 1:
            print("Warning: failed to execute command:")
            print("\t" + final_cmd)
        if failcode > 2:
            exit(1)

@operation
def local_per_host(cmd, **kvargs):
    """Run a command locally, for every defined host.
    
    Like the local() operation, this is pretty similar to 'os.system()', but
    with this operation, the command is executed (and have its variables
    expanded) for each host in fab_hosts.
    
    This operation is defined to take the same keyword arguments as local().
    
    Example:
        local_per_host("scp -i login.key stuff.zip $(fab_host):stuff.zip")
    
    """
    _check_fab_hosts()
    for host in ENV['fab_hosts']:
        ENV['fab_host'] = host
        local(cmd, **kvargs)

@operation
def load(filename, **kvargs):
    """Load up the given fabfile.
    
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
    failcode = _get_failcode(kvargs)
    if os.path.exists(filename):
        execfile(filename)
        for name, obj in locals().items():
            if not name.startswith('_') and isinstance(obj, types.FunctionType):
                COMMANDS[name] = obj
            if not name.startswith('_'):
                __builtins__[name] = obj
    elif failcode > 1:
        print("Warning: Cannot load file '%s'." % filename)
        print("No such file in your current directory.")
        if failcode > 2:
            exit(1)

@operation
def upload_project(**kvargs):
    """Uploads the current project directory to the connected hosts.
    
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
    local("tar -czf %s ." % tar_file, **kvargs)
    put(tar_file, cwd_name + ".tar.gz", **kvargs)
    local("rm -f " + tar_file, **kvargs)
    run("tar -xzf " + cwd_name, **kvargs)
    run("rm -f " + cwd_name + ".tar.gz", **kvargs)

#
# Standard Fabric commands:
#
@command("help")
def _help(**kvargs):
    """Display usage help message to the console, or help for a given command.
    
    You can provide help with a parameter and get more detailed help for a
    specific command. For instance, to learn more about the list command, you
    could run 'fab help:list'.
    
    If you are developing your own fabfile, then you might also be interested
    in learning more about operations. You can do this by running help with the
    'op' parameter set to the name of the operation you would like to learn
    more about. For instance, to learn more about the 'run' operation, you
    could run 'fab help:op=run'.
    
    """
    if kvargs:
        for k, v in kvargs.items():
            if k in COMMANDS:
                _print_help_for_in(k, COMMANDS)
            elif k in OPERATIONS:
                _print_help_for_in(k, OPERATIONS)
            elif k in ['op', 'operation']:
                _print_help_for_in(kvargs[k], OPERATIONS)
            else:
                _print_help_for(k, None)
    else:
        print("""Fabric is a simple pythonic remote deployment tool.
    
    Type 'fab list' to get a list of available commands.
    Type 'fab help:help' to get more information on how to use the built in
    help.
    
    """)

@command("list")
def _list_commands(**kvargs):
    """Display a list of commands with descriptions.
    
    By default, the list command prints a list of available commands, with a
    short description (if one is available). However, the list command can also
    print a list of available operaions if you provide it with the 'ops' or
    'operations' parameter: 'fab list:ops'.
    
    """
    if kvargs:
        for k, v in kvargs.items():
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
                exit(1)
    else:
        print("Available commands are:")
        _list_objs(COMMANDS)

@command("license")
def _license():
    "Display the Fabric distribution license text."
    print """		    GNU GENERAL PUBLIC LICENSE
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
of promoting the sharing and reuse of software generally."""

@command("warranty")
def _warranty():
    "Display warranty information for the Fabric software."
    print """			    NO WARRANTY

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
POSSIBILITY OF SUCH DAMAGES."""

@command("set")
def _set(**kvargs):
    """Set a Fabric variable.
    
    Example:
        $fab set:fab_user=billy,other_var=other_value
    """
    for k, v in kvargs.items():
        ENV[k] = (v % ENV)

@command("shell")
def _shell(**kvargs):
    "Start an interactive shell connection to the specified hosts."
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
# Internal plumbing:
#
def _indent(text, level=4):
    "Indent all lines in text with 'level' number of spaces, default 4."
    return '\n'.join(((' ' * level) + line for line in text.splitlines()))

def _print_help_for(name, doc):
    "Output a pretty-printed help text for the given name & doc"
    default_help_msg = '* No help-text found.'
    print("Help for '%s':\n%s" % (name, _indent(doc or default_help_msg)))

def _print_help_for_in(name, dictionary):
    "Print a pretty help text for the named function in the dict."
    if name in dictionary:
        _print_help_for(name, dictionary[name].__doc__)
    else:
        _print_help_for(name, None)

def _list_objs(objs):
    max_name_len = reduce(lambda a,b: max(a, len(b)), objs.keys(), 0)
    cmds = objs.items()
    cmds.sort(lambda x,y: cmp(x[0], y[0]))
    for name, fn in cmds:
        print '  ', name.ljust(max_name_len),
        if fn.__doc__:
            print ':', fn.__doc__.splitlines()[0]
        else:
            print

def _check_fab_hosts():
    "Check that we have a fab_hosts variable, and complain if it's missing."
    if 'fab_hosts' not in ENV:
        print("Fabric requires a fab_hosts variable.")
        print("Please set it in your fabfile.")
        print("Example: set(fab_hosts=['node1.com', 'node2.com'])")
        exit(1)

def _connect():
    "Populate CONNECTIONS with (hostname, client) tuples as per fab_hosts."
    _check_fab_hosts()
    signal.signal(signal.SIGINT, lambda: _disconnect() and exit(0))
    if 'fab_password' not in ENV:
        print(_lazy_format("Logging into the following hosts as $(fab_user):"))
        print(_indent('\n'.join(ENV['fab_hosts'])))
        ENV['fab_password'] = getpass.getpass()
    else:
        print("Warning: Putting your password in a fabfile is a bad idea.")
    port = int(ENV['fab_port'])
    username = ENV['fab_user']
    password = ENV['fab_password']
    pkey = ENV['fab_pkey']
    key_filename = ENV['fab_key_filename']
    for host in ENV['fab_hosts']:
        client = ssh.SSHClient()
        client.load_system_host_keys()
        if 'fab_new_host_key' in ENV and ENV['fab_new_host_key'] == 'accept':
            client.set_missing_host_key_policy(ssh.AutoAddPolicy())
        client.connect(
            host, port, username, password, pkey, key_filename
        )
        CONNECTIONS.append((host, client))
    if not CONNECTIONS:
        print("The fab_hosts list was empty.")
        print("Please specify some hosts to connect to.")
        exit(1)

def _disconnect():
    "Disconnect all clients."
    global CONNECTIONS
    for host, client in CONNECTIONS:
        client.close()
    CONNECTIONS = []

def _lazy_format(string, env=ENV):
    "Do recursive string substitution of ENV vars - both lazy and earger."
    def replacer_fn(match):
        var = match.group('var')
        if var in env:
            return _lazy_format(env[var] % env, env)
        else:
            return match.group(0)
    return re.sub(_LAZY_FORMAT_SUBSTITUTER, replacer_fn, string % env)

def _on_hosts_do(fn, *args, **kvargs):
    """Invoke the given function with hostname and client parameters in
    accord with the current fac_mode strategy.
    
    fn should be of type:
        (str:hostname, paramiko.SSHClient:clinet) -> bool:success
    
    """
    strategy = ENV['fab_mode']
    if strategy == 'fanout':
        threads = []
        for host, client in CONNECTIONS:
            env = dict(ENV)
            env['fab_host'] = host
            functor = lambda: fn(host, client, env, *args, **kvargs)
            thread = threading.Thread(None, functor)
            thread.setDaemon(True)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
    elif strategy == 'rolling':
        for host, client in CONNECTIONS:
            env = dict(ENV)
            env['fab_host'] = host
            fn(host, client, env, *args)
    else:
        print("Unsupported fab_mode: %s" % strategy)
        print("Supported modes are: fanout, rolling")
        exit(1)

def _put(host, client, env, localpath, remotepath, **kvargs):
    ftp = client.open_sftp()
    localpath = _lazy_format(localpath, env)
    remotepath = _lazy_format(remotepath, env)
    print("[%s] put: %s -> %s" % (host, localpath, remotepath))
    ftp.put(localpath, remotepath)

def _download(host, client, env, remotepath, localpath, **kvargs):
    ftp = client.open_sftp()
    localpath = _lazy_format(localpath) + '.' + host
    remotepath = _lazy_format(remotepath)
    print("[%s] download: %s <- %s" % (host, localpath, remotepath))
    ftp.get(remotepath, localpath)

def _run(host, client, env, cmd, **kvargs):
    cmd = _lazy_format(cmd, env)
    real_cmd = env['fab_shell'] % cmd.replace('"', '\\"')
    print("[%s] run: %s" % (host, (env['fab_debug'] and real_cmd or cmd)))
    stdin, stdout, stderr = client.exec_command(real_cmd)
    out_th = _start_outputter("[%s] out" % host, stdout)
    err_th = _start_outputter("[%s] err" % host, stderr)
    out_th.join()
    err_th.join()

def _sudo(host, client, env, cmd, **kvargs):
    cmd = _lazy_format(cmd, env)
    real_cmd = env['fab_shell'] % ("sudo -S " + cmd.replace('"', '\\"'))
    print("[%s] sudo: %s" % (host, (env['fab_debug'] and real_cmd or cmd)))
    stdin, stdout, stderr = client.exec_command(real_cmd)
    stdin.write(env['fab_password'])
    stdin.write('\n')
    stdin.flush()
    out_th = _start_outputter("[%s] out" % host, stdout)
    err_th = _start_outputter("[%s] err" % host, stderr)
    out_th.join()
    err_th.join()

def _get_failcode(kvarg_map):
    codes = {
        'ignore': 1,
        'warn': 2,
        'abort': 3,
    }
    if 'fail' in kvarg_map:
        return codes[kvarg_map['fail']]
    else:
        return codes['abort']

def _start_outputter(prefix, channel):
    def outputter():
        line = channel.readline()
        while line:
            print("%s: %s" % (prefix, line)),
            line = channel.readline()
    thread = threading.Thread(None, outputter, prefix)
    thread.setDaemon(True)
    thread.start()
    return thread

def _pick_fabfile():
    "Figure out what the fabfile is called."
    guesses = ['fabfile','Fabfile', 'fabfile.py', 'Fabfile.py']
    options = filter(os.path.exists, guesses)
    if options:
        return options[0]
    else:
        return guesses[0] # load() will barf for us...

def _validate_commands(args):
    for cmd in args:
        if cmd.find(':') != -1:
            cmd = cmd.split(':', 1)[0]
        if not cmd in COMMANDS:
            print("No such command: %s" % cmd)
            _list_commands()
            exit(1)
    if not args:
        print("No commands given.")
        _list_commands()

def _execute_commands(args):
    for cmd in args:
        cmd_name = cmd
        cmd_args = None
        if cmd.find(':') != -1:
            cmd_name, cmd_args = cmd.split(':', 1)
        ENV['fab_cur_command'] = cmd_name
        print("Running %s..." % cmd_name)
        if cmd_args is not None:
            cmd_arg_kvs = {}
            for cmd_arg_kv in cmd_args.split(','):
                k, _, v = cmd_arg_kv.partition('=')
                cmd_arg_kvs[k] = (v % ENV)
            COMMANDS[cmd_name](**cmd_arg_kvs)
        else:
            COMMANDS[cmd]()

def main(args):
    try:
        print(__greeter__ % ENV)
        fabfile = _pick_fabfile()
        load(fabfile)
        _validate_commands(args)
        _execute_commands(args)
    finally:
        _disconnect()
        print("Done.")

