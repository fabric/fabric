===============
Getting started
===============

Welcome! This tutorial highlights Fabric's core features; for further details,
see the links within, or the documentation index which has links to conceptual
and API doc sections.


A note about imports
====================

Fabric composes a couple of other libraries as well as providing its own layer
on top; user code will most often import from the ``fabric`` package, but
you'll sometimes import directly from ``invoke`` or ``paramiko`` too:

- `Invoke <https://www.pyinvoke.org>`_  implements CLI parsing, task organization,
  and shell command execution (a generic framework plus specific implementation
  for local commands.)

    - Anything that isn't specific to remote systems tends to live in Invoke,
      and it is often used standalone by programmers who don't need any remote
      functionality.
    - Fabric users will frequently import Invoke objects, in cases where Fabric
      itself has no need to subclass or otherwise modify what Invoke provides.

- `Paramiko <https://www.paramiko.org>`_ implements low/mid level SSH
  functionality - SSH and SFTP sessions, key management, etc.

    - Fabric mostly uses this under the hood; users will only rarely import
      from Paramiko directly.

- Fabric glues the other libraries together and provides its own high level
  objects too, e.g.:

    - Subclassing Invoke's context and command-runner classes, wrapping them
      around Paramiko-level primitives;
    - Extending Invoke's configuration system by using Paramiko's
      ``ssh_config`` parsing machinery;
    - Implementing new high-level primitives of its own, such as
      port-forwarding context managers. (These may, in time, migrate downwards
      into Paramiko.)

.. TODO:
    we should probably rename Collection to be Namespace or something; it's too
    close to 'Connection'


Run commands via Connections and ``run``
========================================

The most basic use of Fabric is to execute a shell command on a remote system
via SSH, then (optionally) interrogate the result. By default, the remote
program's output is printed directly to your terminal, *and* captured. A basic
example:

.. testsetup:: basic

    mock = MockRemote()
    mock.expect(out=b'Linux\n')

.. testcleanup:: basic

    mock.stop()

.. doctest:: basic

    >>> from fabric import Connection
    >>> c = Connection('web1')
    >>> result = c.run('uname -s')
    Linux
    >>> result.stdout.strip() == 'Linux'
    True
    >>> result.exited
    0
    >>> result.ok
    True
    >>> result.command
    'uname -s'
    >>> result.connection
    <Connection host=web1>
    >>> result.connection.host
    'web1'

Meet `.Connection`, which represents an SSH connection and provides the core of
Fabric's API, such as `~.Connection.run`. `.Connection` objects need at least a
hostname to be created successfully, and may be further parameterized by
username and/or port number. You can give these explicitly via args/kwargs::

    Connection(host='web1', user='deploy', port=2202)

Or by stuffing a ``[user@]host[:port]`` string into the ``host`` argument
(though this is purely convenience; always use kwargs whenever ambiguity
appears!)::

    Connection('deploy@web1:2202')

`.Connection` objects' methods (like `~.Connection.run`) usually return
instances of `invoke.runners.Result` (or subclasses thereof) exposing the sorts
of details seen above: what was requested, what happened while the remote
action occurred, and what the final result was.

.. note::
    Many lower-level SSH connection arguments (such as private keys and
    timeouts) can be given directly to the SSH backend by using the
    :ref:`connect_kwargs argument <connect_kwargs-arg>`.

Superuser privileges via auto-response
======================================

Need to run things as the remote system's superuser? You could invoke the
``sudo`` program via `~.Connection.run`, and (if your remote system isn't
configured with passwordless sudo) respond to the password prompt by hand, as
below. (Note how we need to request a remote pseudo-terminal; most ``sudo``
implementations get grumpy at password-prompt time otherwise.)

.. testsetup:: sudo-by-hand

    mock = MockRemote()
    mock.expect(commands=(
        Command(out=b'[sudo] password:\n'),
        Command(out=b'1001\n'),
    ))

.. testcleanup:: sudo-by-hand

    mock.stop()

.. doctest:: sudo-by-hand

    >>> from fabric import Connection
    >>> c = Connection('db1')
    >>> c.run('sudo useradd mydbuser', pty=True)
    [sudo] password:
    <Result cmd='sudo useradd mydbuser' exited=0>
    >>> c.run('id -u mydbuser')
    1001
    <Result cmd='id -u mydbuser' exited=0>

Giving passwords by hand every time can get old; thankfully Invoke's powerful
command-execution functionality includes the ability to :ref:`auto-respond
<autoresponding>` to program output with pre-defined input. We can use this for
``sudo``:

.. testsetup:: sudo-with-responses

    mock = MockRemote()
    mock.expect(out=b'[sudo] password:\nroot\n', in_=b'mypassword\n')

.. testcleanup:: sudo-with-responses

    mock.stop()

.. doctest:: sudo-with-responses

    >>> from invoke import Responder
    >>> from fabric import Connection
    >>> c = Connection('host')
    >>> sudopass = Responder(
    ...     pattern=r'\[sudo\] password:',
    ...     response='mypassword\n',
    ... )
    >>> c.run('sudo whoami', pty=True, watchers=[sudopass])
    [sudo] password:
    root
    <Result cmd='sudo whoami' exited=0>

It's difficult to show in a snippet, but when the above was executed, the user
didn't need to type anything; ``mypassword`` was sent to the remote program
automatically. Much easier!

The ``sudo`` helper
-------------------

Using watchers/responders works well here, but it's a lot of boilerplate to set
up every time - especially as real-world use cases need more work to detect
failed/incorrect passwords.

To help with that, Invoke provides a `Context.sudo
<invoke.context.Context.sudo>` method which handles most of the boilerplate for
you (as `.Connection` subclasses `~invoke.context.Context`, it gets this method
for free.) `~invoke.context.Context.sudo` doesn't do anything users can't do
themselves - but as always, common problems are best solved with commonly
shared solutions.

All the user needs to do is ensure the ``sudo.password`` :doc:`configuration
value </concepts/configuration>` is filled in (via config file, environment
variable, or :option:`--prompt-for-sudo-password`) and `.Connection.sudo`
handles the rest. For the sake of clarity, here's an example where a
library/shell user performs their own `getpass`-based password prompt:

.. testsetup:: sudo

    from __future__ import print_function
    from mock import patch
    gp_patcher = patch('getpass.getpass', side_effect=lambda x: print(x))
    gp_patcher.start()
    mock = MockRemote()
    mock.expect(commands=(
        Command(out=b'root\n'),
        Command(),
        Command(out=b'1001\n'),
    ))

.. testcleanup:: sudo

    mock.stop()
    gp_patcher.stop()

.. doctest:: sudo
    :options: +ELLIPSIS

    >>> import getpass
    >>> from fabric import Connection, Config
    >>> sudo_pass = getpass.getpass("What's your sudo password?")
    What's your sudo password?
    >>> config = Config(overrides={'sudo': {'password': sudo_pass}})
    >>> c = Connection('db1', config=config)
    >>> c.sudo('whoami', hide='stderr')
    root
    <Result cmd="...whoami" exited=0>
    >>> c.sudo('useradd mydbuser')
    <Result cmd="...useradd mydbuser" exited=0>
    >>> c.run('id -u mydbuser')
    1001
    <Result cmd='id -u mydbuser' exited=0>

We filled in the sudo password up-front at runtime in this example; in
real-world situations, you might also supply it via the configuration system
(perhaps using environment variables, to avoid polluting config files), or
ideally, use a secrets management system.


Transfer files
==============

Besides shell command execution, the other common use of SSH connections is
file transfer; `.Connection.put` and `.Connection.get` exist to fill this need.
For example, say you had an archive file you wanted to upload:

.. testsetup:: transfers

    mock = MockSFTP()

.. testcleanup:: transfers

    mock.stop()

.. doctest:: transfers

    >>> from fabric import Connection
    >>> result = Connection('web1').put('myfiles.tgz', remote='/opt/mydata/')
    >>> print("Uploaded {0.local} to {0.remote}".format(result))
    Uploaded /local/myfiles.tgz to /opt/mydata/

These methods typically follow the behavior of ``cp`` and ``scp``/``sftp`` in
terms of argument evaluation - for example, in the above snippet, we omitted
the filename part of the remote path argument.


Multiple actions
================

One-liners are good examples but aren't always realistic use cases - one
typically needs multiple steps to do anything interesting. At the most basic
level, you could do this by calling `.Connection` methods multiple times::

    from fabric import Connection
    c = Connection('web1')
    c.put('myfiles.tgz', '/opt/mydata')
    c.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')

You could (but don't have to) turn such blocks of code into functions,
parameterized with a `.Connection` object from the caller, to encourage reuse::

    def upload_and_unpack(c):
        c.put('myfiles.tgz', '/opt/mydata')
        c.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')
        
As you'll see below, such functions can be handed to other API methods to
enable more complex use cases as well.


Multiple servers
================

Most real use cases involve doing things on more than one server. The
straightforward approach could be to iterate over a list or tuple of
`.Connection` arguments (or `.Connection` objects themselves, perhaps via
``map``)::

    >>> from fabric import Connection
    >>> for host in ('web1', 'web2', 'mac1'):
    >>>     result = Connection(host).run('uname -s')
    ...     print("{}: {}".format(host, result.stdout.strip()))
    ...
    ...
    web1: Linux
    web2: Linux
    mac1: Darwin
    
This approach works, but as use cases get more complex it can be
useful to think of a collection of hosts as a single object. Enter `.Group`, a
class wrapping one-or-more `.Connection` objects and offering a similar API;
specifically, you'll want to use one of its concrete subclasses like
`.SerialGroup` or `.ThreadingGroup`.

The previous example, using `.Group` (`.SerialGroup` specifically), looks like
this::

    >>> from fabric import SerialGroup as Group
    >>> results = Group('web1', 'web2', 'mac1').run('uname -s')
    >>> print(results)
    <GroupResult: {
        <Connection 'web1'>: <CommandResult 'uname -s'>,
        <Connection 'web2'>: <CommandResult 'uname -s'>,
        <Connection 'mac1'>: <CommandResult 'uname -s'>,
    }>
    >>> for connection, result in results.items():
    ...     print("{0.host}: {1.stdout}".format(connection, result))
    ...
    ...
    web1: Linux
    web2: Linux
    mac1: Darwin

Where `.Connection` methods return single ``Result`` objects (e.g.
`fabric.runners.Result`), `.Group` methods return `.GroupResult` - `dict`-like
objects offering access to individual per-connection results as well as
metadata about the entire run.

When any individual connections within the `.Group` encounter errors, the
`.GroupResult` is lightly wrapped in a `.GroupException`, which is raised. Thus
the aggregate behavior resembles that of individual `.Connection` methods,
returning a value on success or raising an exception on failure.


Bringing it all together
========================

Finally, we arrive at the most realistic use case: you've got a bundle of
commands and/or file transfers and you want to apply it to multiple servers.
You *could* use multiple `.Group` method calls to do this::

    from fabric import SerialGroup as Group
    pool = Group('web1', 'web2', 'web3')
    pool.put('myfiles.tgz', '/opt/mydata')
    pool.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')

That approach falls short as soon as logic becomes necessary - for example, if
you only wanted to perform the copy-and-untar above when ``/opt/mydata`` is
empty. Performing that sort of check requires execution on a per-server basis.

You could fill that need by using iterables of `.Connection` objects (though
this foregoes some benefits of using `Groups <.Group>`)::

    from fabric import Connection
    for host in ('web1', 'web2', 'web3'):
        c = Connection(host)
        if c.run('test -f /opt/mydata/myfile', warn=True).failed:
            c.put('myfiles.tgz', '/opt/mydata')
            c.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')

Alternatively, remember how we used a function in that earlier example? You can
go that route instead::

    from fabric import SerialGroup as Group

    def upload_and_unpack(c):
        if c.run('test -f /opt/mydata/myfile', warn=True).failed:
            c.put('myfiles.tgz', '/opt/mydata')
            c.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')

    for connection in Group('web1', 'web2', 'web3'):
        upload_and_unpack(connection)

The only convenience this final approach lacks is a useful analogue to
`.Group.run` - if you want to track the results of all the
``upload_and_unpack`` call as an aggregate, you have to do that yourself. Look
to future feature releases for more in this space!


Addendum: the ``fab`` command-line tool
=======================================

It's often useful to run Fabric code from a shell, e.g. deploying applications
or running sysadmin jobs on arbitrary servers. You could use regular
:ref:`Invoke tasks <defining-and-running-task-functions>` with Fabric library
code in them, but another option is Fabric's own "network-oriented" tool,
``fab``.

``fab`` wraps Invoke's CLI mechanics with features like host selection, letting
you quickly run tasks on various servers - without having to define ``host``
kwargs on all your tasks or similar.

.. note::
    This mode was the primary API of Fabric 1.x; as of 2.0 it's just a
    convenience. Whenever your use case falls outside these shortcuts, it
    should be easy to revert to the library API directly (with or without
    Invoke's less opinionated CLI tasks wrapped around it).

For a final code example, let's adapt the previous example into a ``fab`` task
module called ``fabfile.py``::

    from fabric import task

    @task
    def upload_and_unpack(c):
        if c.run('test -f /opt/mydata/myfile', warn=True).failed:
            c.put('myfiles.tgz', '/opt/mydata')
            c.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')

Not hard - all we did was copy our temporary task function into a file and slap
a decorator on it. `~fabric.tasks.task` tells the CLI machinery to expose the
task on the command line::

    $ fab --list
    Available tasks:

      upload_and_unpack

Then, when ``fab`` actually invokes a task, it knows how to stitch together
arguments controlling target servers, and run the task once per server. To run
the task once on a single server::

    $ fab -H web1 upload_and_unpack

When this occurs, ``c`` inside the task is set, effectively, to
``Connection("web1")`` - as in earlier examples. Similarly, you can give more
than one host, which runs the task multiple times, each time with a different
`.Connection` instance handed in::

    $ fab -H web1,web2,web3 upload_and_unpack
