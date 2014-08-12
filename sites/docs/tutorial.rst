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
    >>> print "Ran {0.command!r} on {0.host}, got this stdout:\n{0.stdout}"
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

Run multiple commands on a server
=================================

Run multiple commands on multiple servers
=========================================

Creating discrete tasks
=======================

Calling tasks from the command line
===================================
