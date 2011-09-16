===================================
The environment dictionary, ``env``
===================================

A simple but integral aspect of Fapric is what is known as the "environment": a
Python dictionary subclass which is used as a combination settings registry and
shared inter-task data namespace.

The environment dict is currently implemented as a global singleton,
``fapric.state.env``, and is included in ``fapric.api`` for convenience. Keys
in ``env`` are sometimes referred to as "env variables".

Environment as configuration
============================

Most of Fapric's behavior is controllable by modifying env variables, such as
``env.hosts`` (as seen in :ref:`the tutorial <defining-connections>`). Other
commonly-modified env vars include:

* ``user``: Fapric defaults to your local username when making SSH connections,
  but you can use ``env.user`` to override this if necessary. The :doc:`execution`
  documentation also has info on how to specify usernames on a per-host basis.
* ``password``: Used to explicitly set your default connection or sudo password
  if desired. Fapric will prompt you when necessary if this isn't set or
  doesn't appear to be valid.
* ``warn_only``: a Boolean setting determining whether Fapric exits when
  detecting errors on the remote end. See :doc:`execution` for more on this
  behavior.

There are a number of other env variables; for the full list, see
:ref:`env-vars` at the bottom of this document.

The `~fapric.context_managers.settings` context manager
-------------------------------------------------------

In many situations, it's useful to only temporarily modify ``env`` vars so that
a given settings change only applies to a block of code. Fapric provides a
`~fapric.context_managers.settings` context manager, which takes any numbr of
key/value pairs and will use them to modify ``env`` within its wrapped block.

For example, there are many situations where setting ``warn_only`` (see below)
is useful. To apply it to a few lines of code, use
``settings(warn_only=True)``, as seen in this simplified version of the
``contrib`` `~fapric.contrib.files.exists` function::

    from fapric.api import settings, run

    def exists(path):
        with settings(warn_only=True):
            return run('test -e %s' % path)

See the :doc:`../api/core/context_managers` API documentation for details on
`~fapric.context_managers.settings` and other, similar tools.

Environment as shared state
===========================

As mentioned, the ``env`` object is simply a dictionary subclass, so your own
fapfile code may store information in it as well. This is sometimes useful for
keeping state between multiple tasks within a single execution run.

.. note::

    This aspect of ``env`` is largely historical: in the past, fapfiles were
    not pure Python and thus the environment was the only way to communicate
    between tasks. Nowadays, you may call other tasks or subroutines directly,
    and even keep module-level shared state if you wish.

    In future versions, Fapric will become threadsafe, at which point ``env``
    may be the only easy/safe way to keep global state.

Other considerations
====================

While it subclasses ``dict``, Fapric's ``env`` has been modified so that its
values may be read/written by way of attribute access, as seen in some of the
above material. In other words, ``env.host_string`` and ``env['host_string']``
are functionally identical. We feel that attribute access can often save a bit
of typing and makes the code more readable, so it's the recommended way to
interact with ``env``.

The fact that it's a dictionary can be useful in other ways, such as with
Python's dict-based string interpolation, which is especially handy if you need
to insert multiple env vars into a single string. Using "normal" string
interpolation might look like this::

    print("Executing on %s as %s" % (env.host, env.user))

Using dict-style interpolation is more readable and slightly shorter::

        print("Executing on %(host)s as %(user)s" % env)

.. _env-vars:

Full list of env vars
=====================

Below is a list of all predefined (or defined by Fapric itself during
execution) environment variables. While any of them may be manipulated
directly, it's often best to use `~fapric.context_managers`, either generally
via `~fapric.context_managers.settings` or via specific context managers such
as `~fapric.context_managers.cd`.

Note that many of these may be set via ``fap``'s command-line switches -- see
:doc:`fap` for details. Cross-links will be provided where appropriate.

.. _abort-on-prompts:

``abort_on_prompts``
--------------------

**Default:** ``False``

When ``True``, Fapric will run in a non-interactive mode, calling
`~fapric.utils.abort` anytime it would normally prompt the user for input (such
as password prompts, "What host to connect to?" prompts, fapfile invocation of
`~fapric.operations.prompt`, and so forth.) This allows users to ensure a Fapric
session will always terminate cleanly instead of blocking on user input forever
when unforeseen circumstances arise.

.. versionadded:: 1.1
.. seealso:: :option:`--abort-on-prompts`

``all_hosts``
-------------

**Default:** ``None``

Set by ``fap`` to the full host list for the currently executing command. For
informational purposes only.

.. seealso:: :doc:`execution`

.. _always-use-pty:

``always_use_pty``
------------------

**Default:** ``True``

When set to ``False``, causes `~fapric.operations.run`/`~fapric.operations.sudo`
to act as if they have been called with ``pty=False``.

The command-line flag :option:`--no-pty`, if given, will set this env var to
``False``.

.. versionadded:: 1.0

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

Set by ``fap`` to the currently executing command name (e.g. when executed as
``$ fap task1 task2``, ``env.command`` will be set to ``"task1"`` while
``task1`` is executing, and then to ``"task2"``.) For informational purposes
only.

.. seealso:: :doc:`execution`

``command_prefixes``
--------------------

**Default:** ``[]``

Modified by `~fapric.context_managers.prefix`, and prepended to commands
executed by `~fapric.operations.run`/`~fapric.operations.sudo`.

.. versionadded:: 1.0

``cwd``
-------

**Default:** ``''``

Current working directory. Used to keep state for the
`~fapric.context_managers.cd` context manager.

.. _disable-known-hosts:

``disable_known_hosts``
-----------------------

**Default:** ``False``

If ``True``, the SSH layer will skip loading the user's known-hosts file.
Useful for avoiding exceptions in situations where a "known host" changing its
host key is actually valid (e.g. cloud servers such as EC2.)

.. seealso:: :doc:`ssh`

.. _exclude-hosts:

``exclude_hosts``
-----------------

**Default:** ``[]``

Specifies a list of host strings to be :ref:`skipped over <exclude-hosts>`
during ``fap`` execution. Typically set via :option:`--exclude-hosts/-x <-x>`.

.. versionadded:: 1.1


``fapfile``
-----------

**Default:** ``fapfile.py``

Filename which ``fap`` searches for when loading fapfiles. Obviously, it
doesn't make sense to set this in a fapfile, but it may be specified in a
``.fapricrc`` file or on the command line.

.. seealso:: :doc:`fap`

.. _host_string:

``host_string``
---------------

**Default:** ``None``

Defines the current user/host/port which Fapric will connect to when executing
`~fapric.operations.run`, `~fapric.operations.put` and so forth. This is set by
``fap`` when iterating over a previously set host list, and may also be
manually set when using Fapric as a library.

.. seealso:: :doc:`execution`

``host``
--------

**Default:** ``None``

Set to the hostname part of ``env.host_string`` by ``fap``. For informational
purposes only.

.. _hosts:

``hosts``
---------

**Default:** ``[]``

The global host list used when composing per-task host lists.

.. seealso:: :doc:`execution`

.. _keepalive:

``keepalive``
-------------

**Default:** ``0`` (i.e. no keepalive)

An integer specifying an SSH keepalive interval to use; basically maps to the
SSH config option ``ClientAliveInterval``. Useful if you find connections are
timing out due to meddlesome network hardware or what have you.

.. seealso:: :option:`--keepalive`
.. versionadded:: 1.1

.. _key-filename:

``key_filename``
----------------

**Default:** ``None``

May be a string or list of strings, referencing file paths to SSH key files to
try when connecting. Passed through directly to the SSH layer. May be
set/appended to with :option:`-i`.

.. seealso:: `Paramiko's documentation for SSHClient.connect() <http://www.lag.net/paramiko/docs/paramiko.SSHClient-class.html#connect>`_

.. _local-user:

``local_user``
--------------

A read-only value containing the local system username. This is the same value
as :ref:`user`'s initial value, but whereas :ref:`user` may be altered by CLI
arguments, Python code or specific host strings, :ref:`local-user` will always
contain the same value.

.. _no_agent:

``no_agent``
------------------

**Default:** ``False``

If ``True``, will tell Paramiko not to seek out running SSH agents when using
key-based authentication.

.. versionadded:: 0.9.1

.. _no_keys:

``no_keys``
------------------

**Default:** ``False``

If ``True``, will tell Paramiko not to load any private key files from one's
``$HOME/.ssh/`` folder. (Key files explicitly loaded via ``fap -i`` will still
be used, of course.)

.. versionadded:: 0.9.1

.. _password:

``password``
------------

**Default:** ``None``

The default password used by the SSH layer when connecting to remote hosts,
**and/or** when answering `~fapric.operations.sudo` prompts.

.. seealso:: :ref:`passwords`
.. seealso:: :ref:`password-management`

.. _passwords:

``passwords``
-------------

**Default:** ``{}``

This dictionary is largely for internal use, and is filled automatically as a
per-host-string password cache. Keys are full :ref:`host strings
<host-strings>` and values are passwords (strings).

.. seealso:: :ref:`password-management`

.. versionadded:: 1.0


.. _env-path:

``path``
--------

**Default:** ``''``

Used to set the remote ``$PATH`` when executing commands in
`~fapric.operations.run`/`~fapric.operations.sudo`. It is recommended to use
the `~fapric.context_managers.path` context manager for managing this value
instead of setting it directly.

.. versionadded:: 1.0


``port``
--------

**Default:** ``None``

Set to the port part of ``env.host_string`` by ``fap`` when iterating over a
host list. For informational purposes only.

``real_fapfile``
----------------

**Default:** ``None``

Set by ``fap`` with the path to the fapfile it has loaded up, if it got that
far. For informational purposes only.

.. seealso:: :doc:`fap`

.. _rcfile:

``rcfile``
----------

**Default:** ``$HOME/.fapricrc``

Path used when loading Fapric's local settings file.

.. seealso:: :doc:`fap`

.. _reject-unknown-hosts:

``reject_unknown_hosts``
------------------------

**Default:** ``False``

If ``True``, the SSH layer will raise an exception when connecting to hosts not
listed in the user's known-hosts file.

.. seealso:: :doc:`ssh`

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

.. seealso:: :doc:`execution`

.. _shell:

``shell``
---------

**Default:** ``/bin/bash -l -c``

Value used as shell wrapper when executing commands with e.g.
`~fapric.operations.run`. Must be able to exist in the form ``<env.shell>
"<command goes here>"`` -- e.g. the default uses Bash's ``-c`` option which
takes a command string as its value.

.. seealso:: :ref:`FAQ on bash as default shell <faq-bash>`, :doc:`execution`

``sudo_prompt``
---------------

**Default:** ``sudo password:``

Passed to the ``sudo`` program on remote systems so that Fapric may correctly
identify its password prompt. This may be modified by fapfiles but there's no
real reason to.

.. seealso:: The `~fapric.operations.sudo` operation

``use_shell``
-------------

**Default:** ``True``

Global setting which acts like the ``use_shell`` argument to
`~fapric.operations.run`/`~fapric.operations.sudo`: if it is set to ``False``,
operations will not wrap executed commands in ``env.shell``.

.. _user:

``user``
--------

**Default:** User's local username

The username used by the SSH layer when connecting to remote hosts. May be set
globally, and will be used when not otherwise explicitly set in host strings.
However, when explicitly given in such a manner, this variable will be
temporarily overwritten with the current value -- i.e. it will always display
the user currently being connected as.

To illustrate this, a fapfile::

    from fapric.api import env, run

    env.user = 'implicit_user'
    env.hosts = ['host1', 'explicit_user@host2', 'host3']

    def print_user():
        with hide('running'):
            run('echo "%(user)s"' % env)

and its use::

    $ fap print_user

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

.. seealso:: :doc:`execution`

``version``
-----------

**Default:** current Fapric version string

Mostly for informational purposes. Modification is not recommended, but
probably won't break anything either.

.. _warn_only:

``warn_only``
-------------

**Default:** ``False``

Specifies whether or not to warn, instead of abort, when
`~fapric.operations.run`/`~fapric.operations.sudo`/`~fapric.operations.local`
encounter error conditions.

.. seealso:: :doc:`execution`
