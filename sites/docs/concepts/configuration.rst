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

- ``port``: TCP port number used by `.Connection` objects when not otherwise
  specified. Default: ``22``.
- ``user``: Username given to the remote ``sshd`` when connecting. Default:
  your local system username.
- ``forward_agent``: Whether to attempt forwarding of your local SSH
  authentication agent to the remote end. Default: ``False`` (same as in
  OpenSSH.)


.. _ssh-config:

Loading and using ``ssh_config`` files
======================================

TK


.. _host-configuration:

Per-host configuration settings
===============================

TK


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
