=====================
Overview and Tutorial
=====================

Welcome to Fabric!

This document is a whirlwind tour of Fabric's features and a quick guide to its
use. In-depth documentation (which is linked to throughout) can be found in
the :doc:`conceptual documentation <concepts>` and the :doc:`API reference
<api>`.


Run a command on a server
=========================

The most basic use of Fabric is to create an SSH connection to a server and
execute a shell command, then (optionally, of course) interrogate the result::

    >>> from fabric import Connection
    >>> result = Connection('web1.example.com').run('uname -s')
    >>> msg = "Ran {0.command!r} on {0.host}, got this stdout:\n{0.stdout}"
    >>> print msg.format(result)
    Ran "uname -s" on web1.example.com, got this stdout:
    Linux

    >>>

Meet `.Connection`, which represents an SSH connection and provides the core of Fabric's API. `.Connection` objects need at least a hostname to be created successfully, and may be further parameterized by username and/or port number. You can give these parameters explicitly via args/kwargs::

    Connection(host='web1', user='deploy', port=2202)

Or you may hand them to the ``host`` argument (which is the first positional
argument) in a format string similar to that used by various other network
tools, ``[user@]host[:port]``::

    Connection('deploy@web1:2202')

.. note::
    If both shorthand and kwarg user/port are given, Fabric `refuses the
    temptation to guess <http://legacy.python.org/dev/peps/pep-0020/>`_ and
    instead raises an exception.

.. seealso::

    * `.Connection` - details on connection setup, including how Fabric
      derives default values for user and port, honors SSH config files, and so
      forth;
    * `.Connection.run` - command invocation specifics, including how to use
      alternate command runners like Invoke's local runner, or remote ``sudo``.

Run a command on multiple servers
=================================

In nontrivial server environments, one frequently has multiple servers serving
the same purpose, or finds a need to run an interrogative action on multiple
servers of varying purposes. To serve this need, Fabric provides a `.Pool`
class wrapping one-or-more `.Connection` objects and offering a similar API.

`.Pool` lets us extend the previous example to a three-server pool::

    >>> from fabric import Pool
    >>> results = Pool('web1', 'web2', 'web3').run('uname -s')
    >>> for connection, result in results.items():
    ...     print "{0.hostname}: {1.stdout}".format(connection, result)
    ...
    ...
    web1: Linux
    web2: Linux
    web3: Linux

    >>>


Run multiple commands on a server
=================================

::
    cxn = Connection('web1')
    cxn.run("uname -s")
    cxn.run("whoami")

Run multiple commands on multiple servers
=========================================

...by command
-------------

::
    pool = Pool('web1', 'web2', 'web3')
    pool.run("uname -s")
    pool.run("whoami")

...by server
------------

Or is there something here we can do with Pool that makes more sense?

::
    for hostname in ('web1', 'web2', 'web3'):
        cxn = Connection(hostname)
        cxn.run("uname -s")
        cxn.run("whoami")

Creating discrete tasks
=======================

Replace these last few examples with something that makes sense as a discrete
unite, e.g. if/else

::
    @task
    def mytask(cxn):
        cxn.run("uname -s")
        cxn.run("whoami")

    mytask.execute() ???
    Executor().execute(mytask) ???

Calling tasks from the command line
===================================

Maybe extend the previous example w/ something that prints usefully?

::
    @task
    def mytask(cxn):
        cxn.run("uname -s")
        cxn.run("whoami")

and then:

::
    $ fab mytask

Wat
===

Deal with discrepancy between full control by default (zero extra printing),
partial printing (print stdout/err only?) and full fab 1 style (print what
you're doing, stdout/stderr, and when you're done - tho maybe never print when
done because that's kinda silly?)
