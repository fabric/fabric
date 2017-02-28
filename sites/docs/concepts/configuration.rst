=============
Configuration
=============

Basics
======

The heart of Fabric's configuration system (as with much of the rest of Fabric)
relies on Invoke functionality, namely `invoke.config.Config` (technically, a
lightweight subclass, `fabric.config.Config`). For practical details on
what this means re: configuring Fabric's behavior, please see :ref:`Invoke's
configuration documentation <invoke:configuration>`.

The primary differences from that document are as follows:

* The configuration file paths sought are all named ``fabric.*`` instead of
  ``invoke.*`` - e.g. ``/etc/fabric.yml`` instead of ``/etc/invoke.yml``,
  ``~/.fabric.py`` instead of ``~/.invoke.py``, etc.
* In addition to :ref:`Invoke's own default configuration values
  <invoke:default-values>`, Fabric merges in some of its own, such as the fact
  that SSH's default port number is 22. See :ref:`default-values` for details.
* Fabric has facilities for loading SSH config files, and will automatically
  create (or update) a configuration subtree on a per `Connection
  <fabric.connection.Connection>` basis, loaded with the interpreted SSH
  configuration for that specific host (since an SSH config file is only ever
  useful via such a lens). See :ref:`ssh-config`.
* Fabric offers a framework for managing per-host and per-host-collection
  configuration details and overrides, which lives under the top-level
  ``hosts`` and ``groups`` config keys; see :ref:`host-configuration`.

    * This functionality supplements that of the SSH config loading described
      earlier; most users will find it preferable to configure as much as
      possible via an SSH config file, but not all Fabric settings have
      ``ssh_config`` analogues, nor do all use cases fit neatly into using such
      files.


.. _default-values:

Default configuration values
============================

Overrides to Invoke-level defaults
----------------------------------

- ``run.replace_env``: ``True``, instead of ``False``, so that remote commands
  run with a 'clean', empty environment instead of inheriting a copy of the
  current process' environment.

  This is for security purposes: leaking local environment data remotely by
  default would be unsanitary. It's also compatible with the behavior of
  OpenSSH.

  .. seealso::
    The warning under `paramiko.channel.Channel.set_environment_variable`.

New default values defined by Fabric
------------------------------------

.. note::
    Most of these settings are also available in the constructor of
    `.Connection`, if they only need modification on a per-connection basis.

.. warning::
    Many of these are also configurable via :ref:`ssh_config files
    <ssh-config>`. **Such values take precedence over those defined via the
    core configuration**, so make sure you're aware of whether you're loading
    such files (or :ref:`disable them to be sure <disabling-ssh-config>`).

- ``connect_kwargs``: Keyword arguments (`dict`) given to `SSHClient.connect
  <paramiko.client.SSHClient.connect>` when `.Connection` performs that method
  call. Default: ``{}``.
- ``forward_agent``: Whether to attempt forwarding of your local SSH
  authentication agent to the remote end. Default: ``False`` (same as in
  OpenSSH.)
- ``gateway``: Used as the default value of the ``gateway`` kwarg for
  `.Connection`. May be any value accepted by that argument. Default: ``None``.
- ``load_openssh_configs``: Whether to automatically seek out :ref:`SSH config
  files <ssh-config>`. When ``False``, no automatic loading occurs. Default:
  ``True``.
- ``port``: TCP port number used by `.Connection` objects when not otherwise
  specified. Default: ``22``.
- ``user``: Username given to the remote ``sshd`` when connecting. Default:
  your local system username.


.. _ssh-config:

Loading and using ``ssh_config`` files
======================================

How files are loaded
--------------------

Fabric uses Paramiko's SSH config file machinery to load and parse
``ssh_config``-format files (following OpenSSH's behavior re: which files to
load, when possible):

- An already-parsed `.SSHConfig` object may be given to `.Config.__init__` via
  its ``ssh_config`` keyword argument; if this value is given, no files are
  loaded, even if they exist.
- A runtime file path may be specified via configuration itself, as the
  ``ssh_config_path`` key; such a path will be loaded into a new `.SSHConfig`
  object at the end of `.Config.__init__` and no other files will be sought
  out.

    - ``ssh_config_path`` is also filled in by the ``fab`` CLI tool if the
      :option:`-F/--ssh-config <-F>` flag is given.

- If no runtime config (object or path) was given to `.Config.__init__`, it
  will automatically seek out and load ``~/.ssh/config`` and/or
  ``/etc/ssh/ssh_config``, if they exist (and in that order.)

  .. note::
      Rules present in both files will result in the user-level file 'winning',
      as the first rule found during lookup is always used.

- If none of the above vectors yielded SSH config data, a blank/empty
  `.SSHConfig` is the final result.
- Regardless of how the object was generated, it is exposed as
  ``Config.base_ssh_config``.

.. _connection-ssh-config:

``Connection``'s use of ``ssh_config`` values
---------------------------------------------

`.Connection` objects expose a per-host 'view' of their config's SSH data
(obtained via `SSHConfig.lookup`) as `.Connection.ssh_config`. `.Connection`
itself references these values as described in the following subsections,
usually as simple defaults for the appropriate config key or parameter
(``port``, ``forward_agent``, etc.)

Unless otherwise specified, these values **override** regular configuration
values for the same keys, but may themselves be overridden by
`.Connection.__init__` parameters.

Take for example a ``~/.fabric.yaml``:

.. code:: yaml

    user: foo

Absent any other configuration, ``Connection('myhost')`` connects as the
``foo`` user.

If we also have an ``~/.ssh/config``::

    Host *
        User bar

then ``Connection('myhost')`` connects as ``bar`` (the SSH config wins over
the Fabric config.)

*However*, in both cases, ``Connection('myhost', user='biz')`` will connect as
``biz``.

.. note::
    The below sections use capitalized versions of ``ssh_config`` keys for
    easier correlation with ``man ssh_config``, **but** the actual `.SSHConfig`
    data structure is normalized to lowercase keys, since SSH config files are
    technically case-insensitive.

Connection parameters
~~~~~~~~~~~~~~~~~~~~~

- ``Hostname``: replaces the original value of ``host`` (which is preserved as
  ``.original_host``.)
- ``Port``: supplies the default value for the ``port`` config option /
  parameter.
- ``User``: supplies the default value for the ``user`` config option /
  parameter.
- ``ConnectTimeout``: sets the default value for the ``timeouts.connect``
  config option / ``timeout`` parameter.

Proxying
~~~~~~~~

- ``ProxyCommand``: supplies default (string) value for ``gateway``.
- ``ProxyJump``: supplies default (`Connection <fabric.connection.Connection>`)
  value for ``gateway``.

.. note::
    If both are specified for a given host, ``ProxyJump`` will override
    ``ProxyCommand``. This is slightly different from OpenSSH, where the order
    the directives are loaded determines which one wins. Doing so on our end
    (where we view the config as a dictionary structure) requires additional
    work.

TK: honor ProxyJump's comma-separated variant, which should translate to
(reverse-ordered) nested Connection-style gateways.

Authentication
~~~~~~~~~~~~~~

- ``ForwardAgent``: controls default behavior of ``forward_agent``.


TK: merge with per-host config when it's figured out


.. _disabling-ssh-config:

Disabling (most) ``ssh_config`` loading
---------------------------------------

Users who need tighter control over how their environment gets configured may
want to disable the automatic loading of system/user level SSH config files;
this can prevent hard-to-expect errors such as a new user's ``~/.ssh/config``
overriding values that are being set in the regular config hierarchy.

To do so, simply set the top level config option ``load_ssh_configs`` to
``False``.

.. note::
    Changing this setting does *not* disable loading of runtime-level config
    files (e.g. via :option:`-F`). If a user is explicitly telling us to load
    such a file, we assume they know what they're doing.


.. _host-configuration:

Per-host configuration settings
===============================


TK:

- Given `.Connection` is the base object, where even would "per-host" data be
  stored / loaded?
    - SSH config loading makes sense for filling uch of this
    - What about regular config? We'd want this data to live separate from the
      core config, so it can't really live in regular config files unless we
      make it a special case (or truly part of the config)
    - But then the question is, where _does_ it come from?
        - Its own set of configuration files, e.g. ``~/.fabric-hosts.yml``
        - Library-only, e.g. ``Config(


----

.. warning:: TODO: EXPANDME

* Fabric simply seeks for specific configuration settings in an Invoke config
  object, either one handed explicitly into its own API objects like Connection
  or Group, or a default one; describe its defaults as we do for Invoke (user,
  port etc).
* Fabric's CLI driver generates Connections and Groups for you and hands in that
  default config (initializing it with CLI options and so forth, just like
  Invoke does)

    * TODO: actually, this means that Invoke's CLI/Executor stuff needs
      further override capability which Fabric's CLI module uses? to wit:

        * additional (or different?) CLI flags like port, user, connection
          related opts
        * different file prefixes, e.g. ~/.fabric.yaml and /etc/fabric.yaml

            * should it ALSO honor invoke files? i.e. find both? What would
              users leveraging both tools expect?

        * override of behavior of default flags, like -f finding a fabfile
          instead of an invoke task file?

* Users who have a nontrivial, non-CLI-based setup (eg celery workers or some
  such) should manage their own 'base' Config file as well as their own
  Connection/Group generation?

    * What would this look like? If I have, say, a 5 module codebase not using
      CLI tasks, where would I store my in-code config settings (or my
      initialization of a Config object which loads conf files - i.e. replacing
      what the CLI module does), and how would I be setting up explicit
      Connections and Groups?

        * E.g. write some sample Jenkins/Celery esque background worker code -
          how does this work, how does it feel?

    * Feels strongly tied to #186 - regardless of whether one has real CLI
      tasks where shared state is in a Context, or if it's non-CLI oriented and
      shared state is "only" in the Config, it is the same problem:

        * What's your code/session entry point?
        * How do you share state throughout a session?
