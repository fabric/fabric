.. _fab-configuration:

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
* Fabric plans to offer a framework for managing per-host and
  per-host-collection configuration details and overrides, though this is not
  yet implemented (it will be analogous to, but improved upon, the
  ``env.hosts`` and ``env.roles`` structures from Fabric 1.x).

    * This functionality will supplement that of the SSH config loading
      described earlier; we expect most users will prefer to configure as much
      as possible via an SSH config file, but not all Fabric settings have
      ``ssh_config`` analogues, nor do all use cases fit neatly into such
      files.


.. _default-values:

Default configuration values
============================

Overrides of Invoke-level defaults
----------------------------------

- ``run.replace_env``: defaults to ``True``, instead of ``False``, so that
  remote commands run with a 'clean', empty environment instead of inheriting
  a copy of the current process' environment.

  This is for security purposes: leaking local environment data remotely by
  default would be unsanitary. It's also compatible with the behavior of
  OpenSSH.

  .. seealso::
    The warning under `paramiko.channel.Channel.set_environment_variable`.

  .. note::
    This is currently accomplished with a keyword argument override, as the
    config setting itself was applying to both ``run`` and ``local``. Future
    updates will ensure the two methods use separate config values.

Extensions to Invoke-level defaults
-----------------------------------

- ``runners.remote``: In Invoke, the ``runners`` tree has a single subkey,
  ``local`` (mapping to `~invoke.runners.Local`). Fabric adds this new subkey,
  ``remote``, which is mapped to `~fabric.runners.Remote`.

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

- ``authentication``: Authentication-related options.

    - ``strategy_class``: If given (defaults to ``None``), must be a subclass
      of `~paramiko.auth_strategy.AuthStrategy`; when not ``None``, triggers
      use of this new Paramiko authentication framework -- see
      :doc:`/concepts/authentication` for what this means, including how it
      relates to ``connect_kwargs``.

- ``connect_kwargs``: Keyword arguments (`dict`) given to `SSHClient.connect
  <paramiko.client.SSHClient.connect>` when `.Connection` performs that method
  call. This is often a way of supplying options Fabric has no native setting
  for. Default: ``{}``.
- ``forward_agent``: Whether to attempt forwarding of your local SSH
  authentication agent to the remote end. Default: ``False`` (same as in
  OpenSSH.)
- ``gateway``: Used as the default value of the ``gateway`` kwarg for
  `.Connection`. May be any value accepted by that argument. Default: ``None``.
- ``load_ssh_configs``: Whether to automatically seek out :ref:`SSH config
  files <ssh-config>`. When ``False``, no automatic loading occurs. Default:
  ``True``.
- ``port``: TCP port number used by `.Connection` objects when not otherwise
  specified. Default: ``22``.
- ``inline_ssh_env``: Boolean serving as global default for the value of
  `.Connection`'s ``inline_ssh_env`` parameter; see its docs for details.
  Default: ``True``.
- ``ssh_config_path``: Runtime SSH config path; see :ref:`ssh-config`. Default:
  ``None``.
- ``timeouts``: Various timeouts, specifically:

    - ``connect``: Connection timeout, in seconds; defaults to ``None``,
      meaning no timeout / block forever.

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

- An already-parsed `~paramiko.config.SSHConfig` object may be given to
  `.Config.__init__` via its ``ssh_config`` keyword argument; if this value is
  given, no files are loaded, even if they exist.
- A runtime file path may be specified via configuration itself, as the
  ``ssh_config_path`` key; such a path will be loaded into a new
  `~paramiko.config.SSHConfig` object at the end of `.Config.__init__` and no
  other files will be sought out.

    - It will be filled in by the ``fab`` CLI tool if the
      :option:`--ssh-config` flag is given.

- If no runtime config (object or path) was given to `.Config.__init__`, it
  will automatically seek out and load ``~/.ssh/config`` and/or
  ``/etc/ssh/ssh_config``, if they exist (and in that order.)

  .. note::
      Rules present in both files will result in the user-level file 'winning',
      as the first rule found during lookup is always used.

- If none of the above vectors yielded SSH config data, a blank/empty
  `~paramiko.config.SSHConfig` is the final result.
- Regardless of how the object was generated, it is exposed as
  ``Config.base_ssh_config``.

.. _connection-ssh-config:

``Connection``'s use of ``ssh_config`` values
---------------------------------------------

`.Connection` objects expose a per-host 'view' of their config's SSH data
(obtained via `~paramiko.config.SSHConfig.lookup`) as `.Connection.ssh_config`.
`.Connection` itself references these values as described in the following
subsections, usually as simple defaults for the appropriate config key or
parameter (``port``, ``forward_agent``, etc.)

Unless otherwise specified, these values override regular configuration values
for the same keys, but may themselves be overridden by `.Connection.__init__`
parameters.

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
    easier correlation with ``man ssh_config``, **but** the actual
    `~paramiko.config.SSHConfig` data structure is normalized to lowercase
    keys, since SSH config files are technically case-insensitive.

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

  - Nested-style ``ProxyJump``, i.e. ``user1@hop1.host,user2@hop2.host,...``,
    will result in an appropriate series of nested ``gateway`` values under the
    hood - as if the user had manually specified ``Connecton(...,
    gateway=Connection('user1@hop1.host',
    gateway=Connection('user2@hop2.host', gateway=...)))``.

.. note::
    If both are specified for a given host, ``ProxyJump`` will override
    ``ProxyCommand``. This is slightly different from OpenSSH, where the order
    the directives are loaded determines which one wins. Doing so on our end
    (where we view the config as a dictionary structure) requires additional
    work.

.. TODO:
    honor ProxyJump's comma-separated variant, which should translate to
    (reverse-ordered) nested Connection-style gateways.

Authentication
~~~~~~~~~~~~~~

- ``ForwardAgent``: controls default behavior of ``forward_agent``.
- ``IdentityFile``: appends to the ``key_filename`` key within
  ``connect_kwargs`` (similar to :option:`--identity`.)

.. TODO: merge with per-host config when it's figured out


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
