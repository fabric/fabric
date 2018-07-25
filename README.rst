What is Fabric?
---------------

Fabric is a high level Python (2.7, 3.4+) library designed to execute shell
commands remotely over SSH, yielding useful Python objects in return:

.. testsetup:: opener

    mock = MockRemote()
    # NOTE: hard to get trailing whitespace in a doctest/snippet block, so we
    # just leave the 'real' newline off here too. Whatever.
    mock.expect(out=b"Linux")

.. testcleanup:: opener

    mock.stop()

.. doctest:: opener

    >>> from fabric import Connection
    >>> result = Connection('web1.example.com').run('uname -s', hide=True)
    >>> msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
    >>> print(msg.format(result))
    Ran 'uname -s' on web1.example.com, got stdout:
    Linux

It builds on top of `Invoke <http://pyinvoke.org>`_ (subprocess command
execution and command-line features) and `Paramiko <http://paramiko.org>`_ (SSH
protocol implementation), extending their APIs to complement one another and
provide additional functionality.

.. note::
    Fabric users may also be interested in two *strictly optional* libraries
    which implement best-practice user-level code: `Invocations
    <https://invocations.readthedocs.io>`_ (Invoke-only, locally-focused CLI
    tasks) and `Patchwork <https://fabric-patchwork.readthedocs.io>`_
    (remote-friendly, typically shell-command-focused, utility functions).

How is it used?
---------------

Core use cases for Fabric include (but are not limited to):

* Single commands on individual hosts:

  .. testsetup:: single-command
  
      from fabric import Connection
      mock = MockRemote()
      mock.expect(out=b"web1")
  
  .. testcleanup:: single-command
  
      mock.stop()
  
  .. doctest:: single-command

      >>> result = Connection('web1').run('hostname')
      web1
      >>> result
      <Result cmd='hostname' exited=0>

* Single commands across multiple hosts (via varying methodologies: serial,
  parallel, etc):

  .. testsetup:: multiple-hosts
  
      from fabric import Connection
      mock = MockRemote()
      mock.expect_sessions(
          Session(host='web1', cmd='hostname', out=b'web1\n'),
          Session(host='web2', cmd='hostname', out=b'web2\n'),
      )
  
  .. testcleanup:: multiple-hosts
  
      mock.stop()
  
  .. doctest:: multiple-hosts

      >>> from fabric import SerialGroup     
      >>> result = SerialGroup('web1', 'web2').run('hostname')
      web1
      web2
      >>> result
      {<Connection host=web1>: <Result cmd='hostname' exited=0>, ...}

* Python code blocks (functions/methods) targeted at individual connections:

  .. testsetup:: tasks
  
      from fabric import Connection
      mock = MockRemote()
      mock.expect(commands=[
          Command("uname -s", out=b"Linux\n"),
          Command("df -h / | tail -n1 | awk '{print $5}'", out=b'33%\n'),
      ])
  
  .. testcleanup:: tasks
  
      mock.stop()
  
  .. doctest:: tasks

      >>> def disk_free(c):
      ...     uname = c.run('uname -s', hide=True)
      ...     if 'Linux' in uname.stdout:
      ...         command = "df -h / | tail -n1 | awk '{print $5}'"
      ...         return c.run(command, hide=True).stdout.strip()
      ...     err = "No idea how to get disk space on {}!".format(uname)
      ...     raise Exit(err)
      ...
      >>> disk_free(Connection('web1'))
      '33%'

* Python code blocks on multiple hosts:

  .. testsetup:: tasks-on-multiple-hosts
  
      from fabric import Connection, SerialGroup
      mock = MockRemote()
      mock.expect_sessions(
        Session(host='web1', commands=[
          Command("uname -s", out=b"Linux\n"),
          Command("df -h / | tail -n1 | awk '{print $5}'", out=b'33%\n'),
        ]),
        Session(host='web2', commands=[
          Command("uname -s", out=b"Linux\n"),
          Command("df -h / | tail -n1 | awk '{print $5}'", out=b'17%\n'),
        ]),
        Session(host='db1', commands=[
          Command("uname -s", out=b"Linux\n"),
          Command("df -h / | tail -n1 | awk '{print $5}'", out=b'2%\n'),
        ]),
      )
  
  .. testcleanup:: tasks-on-multiple-hosts
  
      mock.stop()
  
  .. doctest:: tasks-on-multiple-hosts

      >>> # NOTE: Same code as above!
      >>> def disk_free(c):
      ...     uname = c.run('uname -s', hide=True)
      ...     if 'Linux' in uname.stdout:
      ...         command = "df -h / | tail -n1 | awk '{print $5}'"
      ...         return c.run(command, hide=True).stdout.strip()
      ...     err = "No idea how to get disk space on {}!".format(uname)
      ...     raise Exit(err)
      ...
      >>> {c: disk_free(c) for c in SerialGroup('web1', 'web2', 'db1')}
      {<Connection host=web1>: '33%', <Connection host=web2>: '17%', ...}

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

I'm a user of Fabric 1, how do I upgrade?
-----------------------------------------

We've packaged modern Fabric in a manner that allows installation alongside
Fabric 1, so you can upgrade at whatever pace your use case requires. There are
multiple possible approaches -- see our `detailed upgrade documentation
<http://www.fabfile.org/upgrading.html#upgrading>`_ for details.
