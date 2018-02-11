===================================
The environment dictionary, ``env``
===================================

A simple but integral aspect of Fabric is what is known as the "environment": a
Python dictionary subclass, which is used as a combination settings registry and
shared inter-task data namespace.

The environment dict is currently implemented as a global singleton,
``fabric.state.env``, and is included in ``fabric.api`` for convenience. Keys
in ``env`` are sometimes referred to as "env variables".

Environment as configuration
============================

Most of Fabric's behavior is controllable by modifying ``env`` variables, such
as ``env.hosts`` (as seen in :ref:`the tutorial <defining-connections>`). Other
commonly-modified env vars include:

* ``user``: Fabric defaults to your local username when making SSH connections,
  but you can use ``env.user`` to override this if necessary. The :doc:`execution`
  documentation also has info on how to specify usernames on a per-host basis.
* ``password``: Used to explicitly set your default connection or sudo password
  if desired. Fabric will prompt you when necessary if this isn't set or
  doesn't appear to be valid.
* ``warn_only``: a Boolean setting determining whether Fabric exits when
  detecting errors on the remote end. See :doc:`execution` for more on this
  behavior.

There are a number of other env variables; for the full list, see
:ref:`env-vars` at the bottom of this document.

The `~fabric.context_managers.settings` context manager
-------------------------------------------------------

In many situations, it's useful to only temporarily modify ``env`` vars so that
a given settings change only applies to a block of code. Fabric provides a
`~fabric.context_managers.settings` context manager, which takes any number of
key/value pairs and will use them to modify ``env`` within its wrapped block.

For example, there are many situations where setting ``warn_only`` (see below)
is useful. To apply it to a few lines of code, use
``settings(warn_only=True)``, as seen in this simplified version of the
``contrib`` `~fabric.contrib.files.exists` function::

    from fabric.api import settings, run

    def exists(path):
        with settings(warn_only=True):
            return run('test -e %s' % path)

See the :doc:`../api/core/context_managers` API documentation for details on
`~fabric.context_managers.settings` and other, similar tools.

Environment as shared state
===========================

As mentioned, the ``env`` object is simply a dictionary subclass, so your own
fabfile code may store information in it as well. This is sometimes useful for
keeping state between multiple tasks within a single execution run.

.. note::

    This aspect of ``env`` is largely historical: in the past, fabfiles were
    not pure Python and thus the environment was the only way to communicate
    between tasks. Nowadays, you may call other tasks or subroutines directly,
    and even keep module-level shared state if you wish.

    In future versions, Fabric will become threadsafe, at which point ``env``
    may be the only easy/safe way to keep global state.

Other considerations
====================

While it subclasses ``dict``, Fabric's ``env`` has been modified so that its
values may be read/written by way of attribute access, as seen in some of the
above material. In other words, ``env.host_string`` and ``env['host_string']``
are functionally identical. We feel that attribute access can often save a bit
of typing and makes the code more readable, so it's the recommended way to
interact with ``env``.

The fact that it's a dictionary can be useful in other ways, such as with
Python's ``dict``-based string interpolation, which is especially handy if you
need to insert multiple env vars into a single string. Using "normal" string
interpolation might look like this::

    print("Executing on %s as %s" % (env.host, env.user))

Using dict-style interpolation is more readable and slightly shorter::

        print("Executing on %(host)s as %(user)s" % env)

.. _env-vars:

Full list of env vars
=====================

Below is a list of all predefined (or defined by Fabric itself during
execution) environment variables. While many of them may be manipulated
directly, it's often best to use `~fabric.context_managers`, either generally
via `~fabric.context_managers.settings` or via specific context managers such
as `~fabric.context_managers.cd`.

Note that many of these may be set via ``fab``'s command-line switches -- see
:doc:`fab` for details. Cross-references are provided where appropriate.

.. seealso:: :option:`--set`

.. _abort-exception:

``abort_exception``
-------------------

**Default:** ``None``

Fabric normally handles aborting by printing an error message to stderr and
calling ``sys.exit(1)``. This setting allows you to override that behavior
(which is what happens when ``env.abort_exception`` is ``None``.)

Give it a callable which takes a string (the error message that would have been
printed) and returns an exception instance.  That exception object is then
raised instead of ``SystemExit`` (which is what ``sys.exit`` does.)

Much of the time you'll want to simply set this to an exception class, as those
fit the above description perfectly (callable, take a string, return an
exception instance.) E.g. ``env.abort_exception = MyExceptionClass``.

.. _abort-on-prompts:

``abort_on_prompts``
--------------------

**Default:** ``False``

When ``True``, Fabric will run in a non-interactive mode, calling
`~fabric.utils.abort` anytime it would normally prompt the user for input (such
as password prompts, "What host to connect to?" prompts, fabfile invocation of
`~fabric.operations.prompt`, and so forth.) This allows users to ensure a Fabric
session will always terminate cleanly instead of blocking on user input forever
when unforeseen circumstances arise.

.. versionadded:: 1.1
.. seealso:: :option:`--abort-on-prompts`


``all_hosts``
-------------

**Default:** ``[]``

Set by ``fab`` to the full host list for the currently executing command. For
informational purposes only.

.. seealso:: :doc:`execution`

.. _always-use-pty:

``always_use_pty``
------------------

**Default:** ``True``

When set to ``False``, causes `~fabric.operations.run`/`~fabric.operations.sudo`
to act as if they have been called with ``pty=False``.

.. seealso:: :option:`--no-pty`
.. versionadded:: 1.0

.. _colorize-errors:

``colorize_errors``
-------------------

**Default** ``False``

When set to ``True``, error output to the terminal is colored red and warnings
are colored magenta to make them easier to see.

.. versionadded:: 1.7

.. _combine-stderr:

``combine_stderr``
------------------

**Default**: ``True``

Causes the SSH layer to merge a remote program's stdout and stderr streams to
avoid becoming meshed together when printed. See :ref:`combine_streams` for
details on why this is needed and what its effects are.

.. versionadded:: 1.0

``command``
-----------

**Default:** ``None``

Set by ``fab`` to the currently executing command name (e.g., when executed as
``$ fab task1 task2``, ``env.command`` will be set to ``"task1"`` while
``task1`` is executing, and then to ``"task2"``.) For informational purposes
only.

.. seealso:: :doc:`execution`

``command_prefixes``
--------------------

**Default:** ``[]``

Modified by `~fabric.context_managers.prefix`, and prepended to commands
executed by `~fabric.operations.run`/`~fabric.operations.sudo`.

.. versionadded:: 1.0

.. _command-timeout:

``command_timeout``
-------------------

**Default:** ``None``

Remote command timeout, in seconds.

.. versionadded:: 1.6
.. seealso:: :option:`--command-timeout`

.. _connection-attempts:

``connection_attempts``
-----------------------

**Default:** ``1``

Number of times Fabric will attempt to connect when connecting to a new server. For backwards compatibility reasons, it defaults to only one connection attempt.

.. versionadded:: 1.4
.. seealso:: :option:`--connection-attempts`, :ref:`timeout`

``cwd``
-------

**Default:** ``''``

Current working directory. Used to keep state for the
`~fabric.context_managers.cd` context manager.

.. _dedupe_hosts:

``dedupe_hosts``
----------------

**Default:** ``True``

Deduplicate merged host lists so any given host string is only represented once
(e.g. when using combinations of ``@hosts`` + ``@roles``, or ``-H`` and
``-R``.)

When set to ``False``, this option relaxes the deduplication, allowing users
who explicitly want to run a task multiple times on the same host (say, in
parallel, though it works fine serially too) to do so.

.. versionadded:: 1.5

.. _disable-known-hosts:

``disable_known_hosts``
-----------------------

**Default:** ``False``

If ``True``, the SSH layer will skip loading the user's known-hosts file.
Useful for avoiding exceptions in situations where a "known host" changing its
host key is actually valid (e.g. cloud servers such as EC2.)

.. seealso:: :option:`--disable-known-hosts <-D>`, :doc:`ssh`


.. _eagerly-disconnect:

``eagerly_disconnect``
----------------------

**Default:** ``False``

If ``True``, causes ``fab`` to close connections after each individual task
execution, instead of at the end of the run. This helps prevent a lot of
typically-unused network sessions from piling up and causing problems with
limits on per-process open files, or network hardware.

.. note::
    When active, this setting will result in the disconnect messages appearing
    throughout your output, instead of at the end. This may be improved in
    future releases.

.. _effective_roles:

``effective_roles``
-------------------

**Default:** ``[]``

Set by ``fab`` to the roles list of the currently executing command. For
informational purposes only.

.. versionadded:: 1.9
.. seealso:: :doc:`execution`

.. _exclude-hosts:

``exclude_hosts``
-----------------

**Default:** ``[]``

Specifies a list of host strings to be :ref:`skipped over <exclude-hosts>`
during ``fab`` execution. Typically set via :option:`--exclude-hosts/-x <-x>`.

.. versionadded:: 1.1


``fabfile``
-----------

**Default:** ``fabfile.py``

Filename pattern which ``fab`` searches for when loading fabfiles.
To indicate a specific file, use the full path to the file. Obviously, it
doesn't make sense to set this in a fabfile, but it may be specified in a
``.fabricrc`` file or on the command line.

.. seealso:: :option:`--fabfile <-f>`, :doc:`fab`


.. _gateway:

``gateway``
-----------

**Default:** ``None``

Enables SSH-driven gatewaying through the indicated host. The value should be a
normal Fabric host string as used in e.g. :ref:`env.host_string <host_string>`.
When this is set, newly created connections will be set to route their SSH
traffic through the remote SSH daemon to the final destination.

.. versionadded:: 1.5

.. seealso:: :option:`--gateway <-g>`

.. _kerberos:

``gss_(auth|deleg|kex)``
------------------------

**Default:** ``False`` for all.

These three options (``gss_auth``, ``gss_deleg``, and ``gss_kex``) are passed
verbatim into Paramiko's ``Client.connect`` method, and control
Kerberos/GSS-API behavior. For details, see Paramiko's docs: `GSS-API
authentication <http://docs.paramiko.org/en/latest/api/ssh_gss.html>`_, `GSS-API key exchange <http://docs.paramiko.org/en/latest/api/kex_gss.html>`_.

.. note::
    This functionality requires Paramiko ``1.15`` or above! You will get
    ``TypeError`` about unexpected keyword arguments with Paramiko ``1.14`` or
    earlier, as it lacks Kerberos support.

.. versionadded:: 1.11
.. seealso:: :option:`--gss-auth`, :option:`--gss-deleg`, :option:`--gss-kex`

.. _host_string:

``host_string``
---------------

**Default:** ``None``

Defines the current user/host/port which Fabric will connect to when executing
`~fabric.operations.run`, `~fabric.operations.put` and so forth. This is set by
``fab`` when iterating over a previously set host list, and may also be
manually set when using Fabric as a library.

.. seealso:: :doc:`execution`


.. _forward-agent:

``forward_agent``
--------------------

**Default:** ``False``

If ``True``, enables forwarding of your local SSH agent to the remote end.

.. versionadded:: 1.4

.. seealso:: :option:`--forward-agent <-A>`

.. _host:

``host``
--------

**Default:** ``None``

Set to the hostname part of ``env.host_string`` by ``fab``. For informational
purposes only.

.. _hosts:

``hosts``
---------

**Default:** ``[]``

The global host list used when composing per-task host lists.

.. seealso:: :option:`--hosts <-H>`, :doc:`execution`

.. _keepalive:

``keepalive``
-------------

**Default:** ``0`` (i.e. no keepalive)

An integer specifying an SSH keepalive interval to use; basically maps to the
SSH config option ``ServerAliveInterval``. Useful if you find connections are
timing out due to meddlesome network hardware or what have you.

.. seealso:: :option:`--keepalive`
.. versionadded:: 1.1


.. _key:

``key``
----------------

**Default:** ``None``

A string, or file-like object, containing an SSH key; used during connection
authentication.

.. note::
    The most common method for using SSH keys is to set :ref:`key-filename`.

.. versionadded:: 1.7


.. _key-filename:

``key_filename``
----------------

**Default:** ``None``

May be a string or list of strings, referencing file paths to SSH key files to
try when connecting. Passed through directly to the SSH layer. May be
set/appended to with :option:`-i`.

.. seealso:: `Paramiko's documentation for SSHClient.connect() <http://docs.paramiko.org/en/latest/api/client.html#paramiko.client.SSHClient.connect>`_

.. _env-linewise:

``linewise``
------------

**Default:** ``False``

Forces buffering by line instead of by character/byte, typically when running
in parallel mode. May be activated via :option:`--linewise`. This option is
implied by :ref:`env.parallel <env-parallel>` -- even if ``linewise`` is False,
if ``parallel`` is True then linewise behavior will occur.

.. seealso:: :ref:`linewise-output`

.. versionadded:: 1.3


.. _local-user:

``local_user``
--------------

A read-only value containing the local system username. This is the same value
as :ref:`user`'s initial value, but whereas :ref:`user` may be altered by CLI
arguments, Python code or specific host strings, :ref:`local-user` will always
contain the same value.

.. _no_agent:

``no_agent``
------------

**Default:** ``False``

If ``True``, will tell the SSH layer not to seek out running SSH agents when
using key-based authentication.

.. versionadded:: 0.9.1
.. seealso:: :option:`--no_agent <-a>`

.. _no_keys:

``no_keys``
------------------

**Default:** ``False``

If ``True``, will tell the SSH layer not to load any private key files from
one's ``$HOME/.ssh/`` folder. (Key files explicitly loaded via ``fab -i`` will
still be used, of course.)

.. versionadded:: 0.9.1
.. seealso:: :option:`-k`

.. _output_prefix:

``output_prefix``
-----------------

**Default:** ``True``

By default Fabric prefixes every line of output with either ``[hostname] out:``
or ``[hostname] err:``. Those prefixes may be hidden by setting
``env.output_prefix`` to ``False``.

.. versionadded:: 1.0.0

.. _env-parallel:

``parallel``
-------------------

**Default:** ``False``

When ``True``, forces all tasks to run in parallel. Implies :ref:`env.linewise
<env-linewise>`.

.. versionadded:: 1.3
.. seealso:: :option:`--parallel <-P>`, :doc:`parallel`

.. _password:

``password``
------------

**Default:** ``None``

The default password used by the SSH layer when connecting to remote hosts,
**and/or** when answering `~fabric.operations.sudo` prompts.

.. seealso:: :option:`--initial-password-prompt <-I>`, :ref:`env.passwords <passwords>`, :ref:`password-management`

.. _passwords:

``passwords``
-------------

**Default:** ``{}``

This dictionary is largely for internal use, and is filled automatically as a
per-host-string password cache. Keys are full :ref:`host strings
<host-strings>` and values are passwords (strings).

.. warning::
    If you modify or generate this dict manually, **you must use fully
    qualified host strings** with user and port values. See the link above for
    details on the host string API.

.. seealso:: :ref:`password-management`

.. versionadded:: 1.0


.. _env-path:

``path``
--------

**Default:** ``''``

Used to set the ``$PATH`` shell environment variable when executing commands in
`~fabric.operations.run`/`~fabric.operations.sudo`/`~fabric.operations.local`.
It is recommended to use the `~fabric.context_managers.path` context manager
for managing this value instead of setting it directly.

.. versionadded:: 1.0


.. _pool-size:

``pool_size``
-------------

**Default:** ``0``

Sets the number of concurrent processes to use when executing tasks in parallel.

.. versionadded:: 1.3
.. seealso:: :option:`--pool-size <-z>`, :doc:`parallel`

.. _prompts:

``prompts``
-------------

**Default:** ``{}``

The ``prompts`` dictionary allows users to control interactive prompts. If a
key in the dictionary is found in a command's standard output stream, Fabric
will automatically answer with the corresponding dictionary value.

.. versionadded:: 1.9

.. _port:

``port``
--------

**Default:** ``None``

Set to the port part of ``env.host_string`` by ``fab`` when iterating over a
host list. May also be used to specify a default port.

.. _real-fabfile:

``real_fabfile``
----------------

**Default:** ``None``

Set by ``fab`` with the path to the fabfile it has loaded up, if it got that
far. For informational purposes only.

.. seealso:: :doc:`fab`


.. _remote-interrupt:

``remote_interrupt``
--------------------

**Default:** ``None``

Controls whether Ctrl-C triggers an interrupt remotely or is captured locally,
as follows:

* ``None`` (the default): only `~fabric.operations.open_shell` will exhibit
  remote interrupt behavior, and
  `~fabric.operations.run`/`~fabric.operations.sudo` will capture interrupts
  locally.
* ``False``: even `~fabric.operations.open_shell` captures locally.
* ``True``: all functions will send the interrupt to the remote end.

.. versionadded:: 1.6


.. _rcfile:

``rcfile``
----------

**Default:** ``$HOME/.fabricrc``

Path used when loading Fabric's local settings file.

.. seealso:: :option:`--config <-c>`, :doc:`fab`

.. _reject-unknown-hosts:

``reject_unknown_hosts``
------------------------

**Default:** ``False``

If ``True``, the SSH layer will raise an exception when connecting to hosts not
listed in the user's known-hosts file.

.. seealso:: :option:`--reject-unknown-hosts <-r>`, :doc:`ssh`

.. _system-known-hosts:

``system_known_hosts``
------------------------

**Default:** ``None``

If set, should be the path to a :file:`known_hosts` file.  The SSH layer will
read this file before reading the user's known-hosts file.

.. seealso:: :doc:`ssh`

.. _roledefs:

``roledefs``
------------

**Default:** ``{}``

Dictionary defining role name to host list mappings.

.. seealso:: :doc:`execution`

.. _roles:

``roles``
---------

**Default:** ``[]``

The global role list used when composing per-task host lists.

.. seealso:: :option:`--roles <-R>`, :doc:`execution`

.. _shell:

``shell``
---------

**Default:** ``/bin/bash -l -c``

Value used as shell wrapper when executing commands with e.g.
`~fabric.operations.run`. Must be able to exist in the form ``<env.shell>
"<command goes here>"`` -- e.g. the default uses Bash's ``-c`` option which
takes a command string as its value.

.. seealso:: :option:`--shell <-s>`,
             :ref:`FAQ on bash as default shell <faq-bash>`, :doc:`execution`

.. _skip-bad-hosts:

``skip_bad_hosts``
------------------

**Default:** ``False``

If ``True``, causes ``fab`` (or non-``fab`` use of `~fabric.tasks.execute`) to skip over hosts it can't connect to.

.. versionadded:: 1.4
.. seealso::
    :option:`--skip-bad-hosts`, :ref:`excluding-hosts`, :doc:`execution`


.. _skip-unknown-tasks:

``skip_unknown_tasks``
----------------------

**Default:** ``False``

If ``True``, causes ``fab`` (or non-``fab`` use of `~fabric.tasks.execute`)
to skip over tasks not found, without aborting.

.. seealso::
    :option:`--skip-unknown-tasks`


.. _ssh-config-path:

``ssh_config_path``
-------------------

**Default:** ``$HOME/.ssh/config``

Allows specification of an alternate SSH configuration file path.

.. versionadded:: 1.4
.. seealso:: :option:`--ssh-config-path`, :ref:`ssh-config`

``ok_ret_codes``
------------------------

**Default:** ``[0]``

Return codes in this list are used to determine whether calls to
`~fabric.operations.run`/`~fabric.operations.sudo`/`~fabric.operations.sudo`
are considered successful.

.. versionadded:: 1.6


.. _sudo_password:

``sudo_password``
-----------------

**Default:** ``None``

The default password to submit to ``sudo`` password prompts. If empty or
``None``, :ref:`env.password <password>` and/or :ref:`env.passwords
<passwords>` is used as a fallback.

.. seealso::
    :ref:`password-management`, :option:`--sudo-password`,
    :option:`--initial-sudo-password-prompt`
.. versionadded:: 1.12

.. _sudo_passwords:

``sudo_passwords``
------------------

**Default:** ``{}``

Identical to :ref:`passwords`, but used for sudo-only passwords.

.. seealso:: :ref:`password-management`
.. versionadded:: 1.12

.. _sudo_prefix:

``sudo_prefix``
---------------

**Default:** ``"sudo -S -p '%(sudo_prompt)s' " % env``

The actual ``sudo`` command prefixed onto `~fabric.operations.sudo` calls'
command strings. Users who do not have ``sudo`` on their default remote
``$PATH``, or who need to make other changes (such as removing the ``-p`` when
passwordless sudo is in effect) may find changing this useful.

.. seealso::

    The `~fabric.operations.sudo` operation; :ref:`env.sudo_prompt
    <sudo_prompt>`

.. _sudo_prompt:

``sudo_prompt``
---------------

**Default:** ``"sudo password:"``

Passed to the ``sudo`` program on remote systems so that Fabric may correctly
identify its password prompt.

.. seealso::

    The `~fabric.operations.sudo` operation; :ref:`env.sudo_prefix
    <sudo_prefix>`

.. _sudo_user:

``sudo_user``
-------------

**Default:** ``None``

Used as a fallback value for `~fabric.operations.sudo`'s ``user`` argument if
none is given. Useful in combination with `~fabric.context_managers.settings`.

.. seealso:: `~fabric.operations.sudo`

.. _env-tasks:

``tasks``
-------------

**Default:** ``[]``

Set by ``fab`` to the full tasks list to be executed for the currently
executing command. For informational purposes only.

.. seealso:: :doc:`execution`

.. _timeout:

``timeout``
-----------

**Default:** ``10``

Network connection timeout, in seconds.

.. versionadded:: 1.4
.. seealso:: :option:`--timeout`, :ref:`connection-attempts`

``use_shell``
-------------

**Default:** ``True``

Global setting which acts like the ``shell`` argument to
`~fabric.operations.run`/`~fabric.operations.sudo`: if it is set to ``False``,
operations will not wrap executed commands in ``env.shell``.


.. _use-ssh-config:

``use_ssh_config``
------------------

**Default:** ``False``

Set to ``True`` to cause Fabric to load your local SSH config file.

.. versionadded:: 1.4
.. seealso:: :ref:`ssh-config`


.. _user:

``user``
--------

**Default:** User's local username

The username used by the SSH layer when connecting to remote hosts. May be set
globally, and will be used when not otherwise explicitly set in host strings.
However, when explicitly given in such a manner, this variable will be
temporarily overwritten with the current value -- i.e. it will always display
the user currently being connected as.

To illustrate this, a fabfile::

    from fabric.api import env, run

    env.user = 'implicit_user'
    env.hosts = ['host1', 'explicit_user@host2', 'host3']

    def print_user():
        with hide('running'):
            run('echo "%(user)s"' % env)

and its use::

    $ fab print_user

    [host1] out: implicit_user
    [explicit_user@host2] out: explicit_user
    [host3] out: implicit_user

    Done.
    Disconnecting from host1... done.
    Disconnecting from host2... done.
    Disconnecting from host3... done.

As you can see, during execution on ``host2``, ``env.user`` was set to
``"explicit_user"``, but was restored to its previous value
(``"implicit_user"``) afterwards.

.. note::

    ``env.user`` is currently somewhat confusing (it's used for configuration
    **and** informational purposes) so expect this to change in the future --
    the informational aspect will likely be broken out into a separate env
    variable.

.. seealso:: :doc:`execution`, :option:`--user <-u>`

``version``
-----------

**Default:** current Fabric version string

Mostly for informational purposes. Modification is not recommended, but
probably won't break anything either.

.. seealso:: :option:`--version <-V>`

.. _warn_only:

``warn_only``
-------------

**Default:** ``False``

Specifies whether or not to warn, instead of abort, when
`~fabric.operations` encounter error conditions.

.. seealso:: :option:`--warn-only <-w>`, :doc:`execution`
