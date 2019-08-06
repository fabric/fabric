======================
Command-line interface
======================

This page documents the details of Fabric's command-line interface, ``fab``.


Options & arguments
===================

.. note::
    By default, ``fab`` honors all of the same CLI options as :ref:`Invoke's
    'inv' program <inv>`; only additions and overrides are listed here!

    For example, Fabric implements :option:`--prompt-for-passphrase` and
    :option:`--prompt-for-login-password` because they are SSH specific, but
    it inherits a related option -- :ref:`--prompt-for-sudo-password
    <prompt-for-sudo-password>` -- from Invoke, which handles sudo autoresponse
    concerns.

.. option:: -H, --hosts

    Takes a comma-separated string listing hostnames against which tasks
    should be executed, in serial. See :ref:`runtime-hosts`.

.. option:: -i, --identity

    Overrides the ``key_filename`` value in the ``connect_kwargs`` config
    setting (which is read by `.Connection`, and eventually makes its way into
    Paramiko; see the docstring for `.Connection` for details.)

    Typically this can be thought of as identical to ``ssh -i <path>``, i.e.
    supplying a specific, runtime private key file. Like ``ssh -i``, it builds
    an iterable of strings and may be given multiple times.

    Default: ``[]``.

.. option:: --prompt-for-login-password

    Causes Fabric to prompt 'up front' for a value to store as the
    ``connect_kwargs.password`` config setting (used by Paramiko when
    authenticating via passwords and, in some versions, also used for key
    passphrases.) Useful if you do not want to configure such values in on-disk
    conf files or via shell environment variables.

.. option:: --prompt-for-passphrase

    Causes Fabric to prompt 'up front' for a value to store as the
    ``connect_kwargs.passphrase`` config setting (used by Paramiko to decrypt
    private key files.) Useful if you do not want to configure such values in
    on-disk conf files or via shell environment variables.

.. option:: -S, --ssh-config

    Takes a path to load as a runtime SSH config file. See :ref:`ssh-config`.

.. option:: -t, --connect-timeout

    Takes an integer of seconds after which connection should time out.
    Supplies the default value for the ``timeouts.connect`` config setting.


Seeking & loading tasks
=======================

``fab`` follows all the same rules as Invoke's :ref:`collection loading
<collection-discovery>`, with the sole exception that the default collection
name sought is ``fabfile`` instead of ``tasks``. Thus, whenever Invoke's
documentation mentions ``tasks`` or ``tasks.py``, Fabric substitutes
``fabfile`` / ``fabfile.py``.

For example, if your current working directory is
``/home/myuser/projects/mywebapp``, running ``fab --list`` will cause Fabric to
look for ``/home/myuser/projects/mywebapp/fabfile.py`` (or
``/home/myuser/projects/mywebapp/fabfile/__init__.py`` - Python's import system
treats both the same). If it's not found there,
``/home/myuser/projects/fabfile.py`` is sought next; and so forth.


.. _runtime-hosts:

Runtime specification of host lists
===================================

While advanced use cases may need to take matters into their own hands, you can
go reasonably far with the core :option:`--hosts` flag, which specifies one or
more hosts the given task(s) should execute against.

By default, execution is a serial process: for each task on the command line,
run it once for each host given to :option:`--hosts`. Imagine tasks that simply
print ``Running <task name> on <host>!``::

    $ fab --hosts host1,host2,host3 taskA taskB
    Running taskA on host1!
    Running taskA on host2!
    Running taskA on host3!
    Running taskB on host1!
    Running taskB on host2!
    Running taskB on host3!

.. note::
    When :option:`--hosts` is not given, ``fab`` behaves similarly to Invoke's
    :ref:`command-line interface <inv>`, generating regular instances of
    `~invoke.context.Context` instead of `Connections <.Connection>`.

Executing arbitrary/ad-hoc commands
===================================

``fab`` leverages a lesser-known command line convention and may be called in
the following manner::

    $ fab [options] -- [shell command]

where everything after the ``--`` is turned into a temporary `.Connection.run`
call, and is not parsed for ``fab`` options. If you've specified a host list
via an earlier task or the core CLI flags, this usage will act like a one-line
anonymous task.

For example, let's say you wanted kernel info for a bunch of systems::

    $ fab -H host1,host2,host3 -- uname -a

Such a command is equivalent to the following Fabric library code::

    from fabric import Group

    Group('host1', 'host2', 'host3').run("uname -a")

Most of the time you will want to just write out the task in your fabfile
(anything you use once, you're likely to use again) but this feature provides a
handy, fast way to dash off an SSH-borne command while leveraging predefined
connection settings.
