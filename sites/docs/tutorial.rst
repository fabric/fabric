=====================
Overview and Tutorial
=====================

Welcome! This document is a whirlwind tour of Fabric's features and a quick
guide to its use. In-depth documentation (which is linked to throughout) can be
found in the :doc:`conceptual documentation <concepts>` and the :doc:`API
reference <api>`.

.. note::
    If you're new to Python, we **strongly** recommend checking out `Python's
    own tutorial <https://docs.python.org/2.6/tutorial/index.html>`_ first.


Run commands
============

The most basic use of Fabric is to create an SSH connection to a server and
execute a shell command, then (optionally, of course) interrogate the result::

    >>> from fabric import Connection
    >>> result = Connection('web1').run('uname -s')
    >>> msg = "Ran {0.command!r} on {0.host}, got this stdout:\n{0.stdout}"
    >>> print(msg.format(result))
    Ran "uname -s" on web1, got this stdout:
    Linux

Meet `.Connection`, which represents an SSH connection and provides the core
of Fabric's API. `.Connection` objects need at least a hostname to be created
successfully, and may be further parameterized by username and/or port
number. You can give these parameters explicitly via args/kwargs::

    Connection(host='web1', user='deploy', port=2202)

Or by stuffing a ``[user@]host[:port]`` format string into just the ``host`` argument::

    Connection('deploy@web1:2202')

`.Connection` objects' methods tend to return subclasses of `.Result`, such as
`.CommandResult`, exposing all sorts of data about what action was taken, what
happened during and after it ran, and so forth.


Transfer files
==============

Besides shell command execution, the other common use of SSH connections is
file transfer; `.Connection.put` and `.Connection.get` behave about as you
might expect. For example, say you had an archive file you wanted to upload::

    >>> from fabric import Connection
    >>> result = Connection('web1').put('myfiles.tgz', '/opt/mydata/')
    >>> print("Uploaded {0.local_path} to {0.remote_path}".format(result))
    Uploaded /home/localuser/myproject/myfiles.tgz to /opt/mydata/myfiles.tgz

As with most other file-copying tools (``cp``, ``sftp``, etc) these methods
allow varying shorthands, such as how we omitted the filename part of the
remote path.


Multiple actions
================

The above one-liners are good examples but aren't realistic use cases - one
typically needs multiple steps to do anything interesting. At the most basic
level, you can make a `.Connection` and then call its methods as many times as
needed::

    from fabric import Connection
    cxn = Connection('web1')
    cxn.put('myfiles.tgz', '/opt/mydata')
    cxn.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')

You could (but don't have to) turn such blocks of code into regular Python
functions, parameterized with a `.Connection` object from the caller, to
encourage reuse::

    def upload_and_unpack(cxn):
        cxn.put('myfiles.tgz', '/opt/mydata')
        cxn.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')
        
As you'll see below, such functions can be handed to other API methods to
enable more complex use cases as well.


Multiple servers
================

Many real use cases involve doing things on more than one server. The
straightforward approach in that case is to iterate over a list or tuple of
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
    
This approach is certainly doable, but as use cases get more complex it can be
useful to think of a collection of hosts as a single object. Enter `.Pool`, a
class wrapping one-or-more `.Connection` objects and offering a similar API.

The previous example, using `.Pool`, looks like this::

    >>> from fabric import Pool
    >>> results = Pool('web1', 'web2', 'mac1').run('uname -s')
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

Where `.Connection` methods return singular `.Result` objects (such as
`.CommandResult`), `.Pool` methods return `ResultSets <.ResultSet>` -
`dict`-like objects offering easy access to individual per-connection results
as well as metadata about the entire run.


Bringing it all together
========================

Finally, we arrive at the most realistic use case: you've got a bundle of
commands and/or file transfers and you want to apply it to multiple servers.
You *could* use multiple `.Pool` method calls to do this::

    from fabric import Pool
    pool = Pool('web1', 'web2', 'web3')
    pool.put('myfiles.tgz', '/opt/mydata')
    pool.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')

This quickly falls down once logic enters the picture, such as if the
copy-and-untar action above only needs to happen if ``/opt/mydata`` is
presently empty. Performing that sort of check requires execution on a
per-server basis.

You could fill that need by using iterables of `.Connection` objects (though
this foregoes some of the benefits of using `Pools <.Pool>`)::

    from fabric import Connection
    for host in ('web1', 'web2', 'web3'):
        cxn = Connection(host)
        if cxn.run('test -f /opt/mydata/myfile', warn=True).failed:
            cxn.put('myfiles.tgz', '/opt/mydata')
            cxn.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')

Alternately, remember how we used a function in that earlier example? You can
hand such a function to `.Pool.execute` and get the best of both worlds::

    from fabric import Pool

    def upload_and_unpack(cxn):
        if cxn.run('test -f /opt/mydata/myfile', warn=True).failed:
            cxn.put('myfiles.tgz', '/opt/mydata')
            cxn.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')

    Pool('web1', 'web2', 'web3').execute(upload_and_unpack)

`.Pool.execute`, like its sibling methods, returns `.ResultSet` objects; its
per-connection values are simply the return values of the function passed in.


'Classic' Fabric: the ``fab`` runner
====================================

Earlier versions of Fabric (prior to 2.x) were strongly oriented around the
concept of distributing files containing all your Fabric-using code, called
*fabfiles* (think ``Makefile``) and invoking the tasks within using the ``fab``
command-line tool.

Modern Fabric is designed as a library first and foremost, but thankfully this
doesn't preclude offering CLI-oriented functionality. Details for this
operational mode can be found in :doc:`the concepts section
</concepts/fabfiles>`, but here's a quick teaser.

All prior examples have been purposefully generic - you could run them in a
Python shell, run them from arbitrary Python code, etc. Here, we specifically
make a file called ``fabfile.py`` and place a tweaked copy of the previous
example into it::

    from fabric import task

    @task
    def upload_and_unpack(cxn):
        cxn.put('myfiles.tgz', '/opt/mydata')
        cxn.run('tar -C /opt/mydata -xzvf /opt/mydata/myfiles.tgz')

Note addition of the `~.task` decorator (required to mark the function for
exposure to the CLI) and removal of the ``Pool(...).execute()`` line. At its
heart, Fabric's CLI machinery just provides an easy way to perform runtime
parameterization - in this case, "which host or pool to run against?".

Which brings us to the invocation side::

    $ fab -H web1,web2,web3 upload_and_unpack

This would execute identically to the interactive snippet from the previous
section. The big difference, of course, is the ability to change the list of
hosts given to ``-H``::

    $ fab -H web1 upload_and_unpack
    $ fab -H web1,web3 upload_and_unpack

In addition to creating ad-hoc pools via ``-H``, it's also possible to define
collections of named pools - e.g. defining a ``web`` pool that evaluates to
those same three ``webN`` hosts - and more besides. Again, see :doc:`the
concepts section </concepts/fabfiles>` for details.
