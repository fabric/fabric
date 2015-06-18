What is Fabric?
---------------

Fabric is a high level Python (2.6+, 3.2+) library designed to execute shell
commands remotely over SSH, yielding useful Python objects in return::

    >>> from fabric import Connection
    >>> result = Connection('web1.example.com').run('uname -s')
    >>> msg = "Ran {0.command!r} on {0.host}, got this stdout:\n{0.stdout}"
    >>> print(msg.format(result))
    Ran "uname -s" on web1.example.com, got this stdout:
    Linux

It builds on top of `Invoke <http://pyinvoke.org>`_ (command execution
interfaces and optional command-line features) and `Paramiko
<http://paramiko.org>`_ (SSH protocol implementation), extending their APIs to
complement one another and provide additional functionality.

How is it used?
---------------

Core use cases for Fabric include (but are not limited to):

* Single commands on individual hosts::

      >>> Connection('web1').run('whoami')
      <Result>

* Single commands across multiple hosts (via varying methodologies: serial,
  parallel, etc)::

      >>> Group(['web1', 'web2', 'db1']).run('df -h')
      {<Host>: <Result>, ...}

* Python code blocks (functions/methods) on individual hosts::

      >>> def disk_free(ctx):
      >>>     uname = ctx.run('uname -s')
      >>>     if 'Linux' in uname:
      ...         command = "df -h / | tail -n1 | awk '{print $5}'"
      ...         return ctx.run(command).stdout
      ...     err = "No idea how to get disk space on {0}!".format(uname)
      ...     raise Exception(err)
      ...
      >>> Connection('web1').execute(disk_free)
      33%

* Python code blocks on multiple hosts::

      >>> def disk_free(ctx):
      ...     # ...
      ...
      >>> Group(['db1', 'db2', 'web1', 'lb1']).execute(disk_free)
      {<Host>: "33%", ...}

In addition to these library-oriented use cases, Fabric makes it easy to
integrate with Invoke's command-line task functionality, invoking via a ``fab``
binary stub:

* Python functions, methods or entire objects can be used as CLI-addressable
  tasks, e.g. ``fab deploy``;
* Tasks may indicate other tasks to be run before or after they themselves
  execute (pre- or post-tasks);
* Tasks are parameterized via regular GNU-style arguments, e.g. ``fab deploy
  --env=prod -d``;
* Multiple tasks may be given in a single CLI session, e.g. ``fab build
  deploy``;
* Much more - all other Invoke functionality is supported - see `its
  documentation <http://docs.pyinvoke.org>`_ for details.
