========
Tutorial
========

Welcome! This tutorial highlights Fabric's core features. In-depth
documentation (linked throughout) can be found in the :doc:`conceptual
documentation <concepts>` and the :doc:`API reference <api>`.

.. note::
    If you're new to Python, we **strongly** recommend checking out `Python's
    own tutorial <https://docs.python.org/2.6/tutorial/index.html>`_ first.

Prelude: Fabric and its relation to Invoke
==========================================

It's important to note that as of 2.0, Fabric is really two libraries working
together:

* `Invoke <https://pyinvoke.org>`_, which defines general interfaces (how CLI
  tasks work, what executing shell commands looks like, etc) and implements
  "local"-specific functionality (executing shell commands on the local host);
* Fabric itself, which extends Invoke's interfaces where necessary
  (implementing remote shell execution) and adds functionality with no local
  analogue (such as file upload/download).

    * Most of the network functionality uses `Paramiko <https://paramiko.org>`_
      under the hood - but most users will never need to import anything from
      Paramiko directly.

Because of this, most imports will be from the ``fabric`` namespace (such as
``from fabric import Connection``) -- but occasionally you'll import directly
from ``invoke`` when Fabric's not overriding anything. For example, when
constructing task namespaces, you'll see ``from invoke import Collection``.

.. TODO:
    we should probably rename Collection to be Namespace or something; it's too
    close to 'Connection'


Run commands
============

The most basic use of Fabric is to execute a shell command on a server (via
SSH), then (optionally) interrogate the result::


    >>> from fabric import Connection
    >>> result = Connection('web1').run('uname -s')
    >>> print(result.host)
    web1
    >>> print(result.command)
    uname -s
    >>> print(result.stdout.strip())
    Linux

Meet `.Connection`, which represents an SSH connection and provides the core
of Fabric's API. `.Connection` objects need at least a hostname to be created
successfully, and may be further parameterized by username and/or port
number. You can give these explicitly via args/kwargs::

    Connection(host='web1', user='deploy', port=2202)

Or by stuffing a ``[user@]host[:port]`` string into the ``host`` argument
(though this is purely convenience; always use kwargs whenever ambiguity
appears!)::

    Connection('deploy@web1:2202')

`.Connection` objects' methods usually return instances of
`invoke.runners.Result` (or subclasses thereof) exposing the sorts of details
seen above: what was requested, what happened while the remote action occurred,
and what the final result was.


Superuser privileges
====================

blah blah you can also run via sudo() which is identical to run() but which
sets command wrapper (how to do that in invoke?) to 'sudo -c xxx', and
sets autoresponse to sudo prompt + <config for password, wherever that
lives...needs to be per-host + default>

(This means we need another Invoke ticket for command wrapping, unless one
already exists...)

Include explicit note that both command wrapping and autoresponse can be set by
hand with regular ol' run() if desired, sudo() is simply a convenience.

.. TODO:
    and apparently sudo _requires_ pty=True to work well, if a password is
    needed. grump. figure out realistic shit around this: always pty when sudo;
    default to pty generally (starting to seem like maybe the right approach so
    far...maybe)  since differing between sudo and run is dumb; figure out if
    we can force sudo to 'ask' stderr even if it thinks no terminal is
    there; ???

.. TODO: ohhh that's why we used -S, so...try that first lolllll


Transfer files
==============

Besides shell command execution, the other common use of SSH connections is
file transfer; `.Connection.put` and `.Connection.get` exist to fill this need.
For example, say you had an archive file you wanted to upload::

    >>> from fabric import Connection
    >>> result = Connection('web1').put('myfiles.tgz', remote='/opt/mydata/')
    >>> print("Uploaded {0.local_path} to {0.remote_path}".format(result))
    Uploaded /home/localuser/myproject/myfiles.tgz to /opt/mydata/myfiles.tgz

These methods typically follow the behavior of ``cp`` and ``scp``/``sftp`` in
terms of argument evaluation - for example, in the above snippet, we omitted
the filename part of the remote path argument.


Multiple actions
================

One-liners are good examples but aren't always realistic use cases - one
typically needs multiple steps to do anything interesting. At the most basic
level, you could do this by calling `.Connection` methods multiple times::

    from fabric import Connection
    cxn = Connection('web1')
    cxn.put('myfiles.tgz', '/opt/mydata')
    cxn.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')

You could (but don't have to) turn such blocks of code into functions,
parameterized with a `.Connection` object from the caller, to encourage reuse::

    def upload_and_unpack(cxn):
        cxn.put('myfiles.tgz', '/opt/mydata')
        cxn.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')
        
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
    ...     print("{0}: {1}".format(host, result.stdout.strip()))
    ...
    ...
    web1: Linux
    web2: Linux
    mac1: Darwin
    
This approach works, but as use cases get more complex it can be
useful to think of a collection of hosts as a single object. Enter `.Group`, a
class wrapping one-or-more `.Connection` objects and offering a similar API.

The previous example, using `.Group`, looks like this::

    >>> from fabric import Group
    >>> results = Group('web1', 'web2', 'mac1').run('uname -s')
    >>> print(results)
    <ResultSet: {
        <Connection 'web1'>: <CommandResult 'uname -s'>,
        <Connection 'web2'>: <CommandResult 'uname -s'>,
        <Connection 'mac1'>: <CommandResult 'uname -s'>
    }>
    >>> for connection, result in results.items():
    ...     print("{0.hostname}: {1.stdout}".format(connection, result))
    ...
    ...
    web1: Linux
    web2: Linux
    mac1: Darwin

Where `.Connection` methods return single ``Result`` objects (e.g.
`fabric.runners.Result`), `.Group` methods return ``ResultSets`` -
`dict`-like objects offering access to individual per-connection results as
well as metadata about the entire run.


Bringing it all together
========================

Finally, we arrive at the most realistic use case: you've got a bundle of
commands and/or file transfers and you want to apply it to multiple servers.
You *could* use multiple `.Group` method calls to do this::

    from fabric import Group
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
        cxn = Connection(host)
        if cxn.run('test -f /opt/mydata/myfile', warn=True).failed:
            cxn.put('myfiles.tgz', '/opt/mydata')
            cxn.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')

Alternatively, remember how we used a function in that earlier example? You can
hand such a function to ``Group.execute`` and get the best of both worlds::

    from fabric import Group

    def upload_and_unpack(cxn):
        if cxn.run('test -f /opt/mydata/myfile', warn=True).failed:
            cxn.put('myfiles.tgz', '/opt/mydata')
            cxn.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')

    Group('web1', 'web2', 'web3').execute(upload_and_unpack)

``Group.execute``, like its sibling methods, returns ``ResultSet`` objects; its
per-connection values are simply the return values of the function passed in.


Addendum: the ``fab`` command-line tool
=======================================

It's often useful to run Fabric code from a shell, e.g. deploying applications
or running sysadmin jobs on arbitrary servers. You could use regular
:ref:`Invoke tasks <defining-and-running-task-functions>` with Fabric library
code in them, but another option is Fabric's own "network-oriented" tool,
``fab``.

``fab`` wraps Invoke's CLI mechanics with features like host selection, letting
you quickly run tasks on various servers - without having to e.g. define
``host`` kwargs on all your tasks.

.. note::
    This mode was the primary API of Fabric 1.x; as of 2.0 it's just a
    convenience. Whenever your use case falls outside these shortcuts, it
    should be easy to revert to the library API directly (with or without
    Invoke's less opinionated CLI tasks).

For a final code example, let's adapt the previous one into a ``fab`` task
module called ``fabfile.py``::

    from invoke import task

    @task
    def upload_and_unpack(cxn):
        if cxn.run('test -f /opt/mydata/myfile', warn=True).failed:
            cxn.put('myfiles.tgz', '/opt/mydata')
            cxn.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')

Not hard - all we did was copy our temporary task function into a file and slap
a decorator on it. `~invoke.tasks.task` tells the CLI machinery to expose the
task on the command line::

    $ fab --list
    Available tasks:

      upload_and_unpack

Then, when ``fab`` actually invokes a task, it knows how to stitch together
arguments controlling target servers, and run the task once per server. To run
the task once on a single server::

    $ fab -H web1 upload_and_unpack

When this occurs, ``cxn`` inside the task is set, effectively, to
``Connection("web1")`` - as in earlier examples. Similarly, you can give more
than one host, which creates a `.Group` under the hood and uses its
`~.Group.execute` method::

    $ fab -H web1,web2,web3 upload_and_unpack

This is just the start; see TODO: other docs, for details.
