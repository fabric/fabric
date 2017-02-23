=========================
Upgrading from Fabric 1.x
=========================

Fabric 2 represents a near-total reimplementation & reorganization of the
software. It's been broken in two, cleaned up, made more explicit, and so
forth. In some cases, upgrading requires only basic search & replace; in
others, more work is needed.

If you read this document carefully, it should guide you in the right direction
until you're fully upgraded. Should anything be missing, please file a ticket
`on Github <https://github.com/fabric/fabric>`_ and we'll update it ASAP.

General / conceptual
====================

- All of Fabric 1's non-SSH-specific functionality (CLI parsing, task
  organization, command execution basics, etc) has been moved to a more general
  library called `Invoke <http://pyinvoke.org>`_. Fabric 2 builds on Invoke
  (and as before, on Paramiko) to present an SSH-specific API.
- The CLI task-oriented workflow remains a primary design goal, but the library
  use case is no longer a second-class citizen; instead, the library
  functionality has been designed first, with the CLI/task features built on
  top of it.
- Invoke's design includes `explicit user-facing testing functionality
  <testing-user-code>`; if you didn't find a way to write tests for your
  Fabric-using code before, it should be much easier now.

    - We recommend trying to write tests early on; they will help clarify the
      upgrade process for you & also make the process safer!

API organization
================

- There's no longer a need to import everything through ``fabric.api``; all
  useful imports are now available at the top level, e.g. ``from fabric import
  Connection``.
- Speaking of: the primary API is now "instantiate `.Connection` objects and
  call their methods" instead of "manipulate global state and call module-level
  functions."
- Connections replace *host strings*, which are no longer first-order
  primitives but simply convenient shorthand in a few spots.
- Connection objects store per-connection state such as user, hostname, gateway
  config, etc, and encapsulate low-level objects from Paramiko (such as their
  ``SSHClient`` instance.)
- Other configuration state (such as default desired behavior, authentication
  parameters, etc) can also be stored in these objects, and will affect how
  they operate. This configuration is also inherited from the CLI machinery
  when the latter is in use.
- The basic "respond to prompts" functionality found as Fabric 1's
  ``env.prompts`` dictionary option, has been significantly fleshed out into a
  framework of :ref:`Watchers <autoresponding>` which operate on a running
  command's input and output streams.

    - In addition, ``sudo`` has been rewritten to use that framework; while
      it's still useful to have implemented in Fabric (actually Invoke) itself,
      it doesn't use any private internals any longer.

- *Roles* (and other lists-of-host-strings such as the result of using ``-H``
  on the CLI) are implemented via `.Group` objects, which are lightweight
  wrappers around multiple Connections.

.. TODO:
    how will we support roles on the CLI or otherwise? 100% user-driven? Show
    an example of how to implement fabric 1's roles with a basic one-level
    dict, maybe?

CLI tasks
=========

- Fabric-specific command-line tasks now take a `.Connection` object as their
  first positional argument.
  
    - This sacrifices some of the "quick DSL" of v1 in exchange for a
      significantly cleaner, easier to understand/debug, and more
      user-overrideable, API structure.
    - It also lessens the distinction between "a module of functions" and "a
      class of methods"; users can more easily start with the former and
      migrate to the latter when their needs grow/change.

- Old-style task functions (those not decorated with ``@task``) are gone. You
  must now always use ``@task``.

.. TODO:
    how to handle 'local-only' tasks exactly? have both @task decorators
    imported at the same time? just use the remote one (like fabric 1
    effectively did)? use invoke solely for CLI and import fabric solely as a
    library? (should we recommend that?)

Remote shell commands
=====================

- There is no more built-in "use shell" or "shell" option - if your remote sshd
  isn't wrapping commands in a shell execution (most of them do) use the new
  command processing framework to add your own to taste.

Networking
==========

- ``env.gateway`` is now the ``gateway`` kwarg to `.Connection`, and -- for
  ``ProxyJump`` style gateways -- should be another `.Connection` object
  instead of a host string.

    - **New:** You may specify a runtime, non-SSH-config-driven
      ``ProxyCommand``-style string as the ``gateway`` kwarg instead, which
      will act just like a regular ``ProxyCommand``.
    - SSH-config-driven ``ProxyCommand`` continues to work as it did in v1.

- ``fabric.context_managers.remote_tunnel`` (which forwards a locally
  visible/open port to the remote end so remote processes may connect to it) is
  now `.Connection.forward_local`.
- Accompanying `.Connection.forward_local` is the logical inversion,
  `.Connection.forward_remote` (forwards a remotely visible port locally),
  which is new in Fabric 2 and was not implemented in Fabric 1 at time of
  writing (though there are patches for it).

.. TODO:
    how to perform "setup" or "pre-execution" things like dynamically setting a
    "host list", where 'fab foo bar' wants 'foo' to change 'bar's context
    somehow? (Especially, what about 'fab foo bar biz baz' - can't simply tell
    'foo' to run 'bar' with some hardcoded params or anything.)

Configuration
=============

- General configuration has been massively improved over the old ``fabricrc``
  files; Fabric 2 builds on Invoke which offers a full-fledged configuration
  hierarchy (in-code config, multiple config file locations, environment
  variables, and CLI flags) and multiple file formats. See Invoke's
  configuration documentation for details.
- :ref:`SSH config file loading <ssh-config>` has also improved. Fabric 1
  allowed selecting a single SSH config file; version 2 behaves more like
  OpenSSH and will seek out both system and user level config files, as well as
  allowing a runtime config file. (And advanced users may simply supply their
  own Paramiko SSH config object they obtained however.)
- Speaking of SSH config loading, it is **now enabled by default**, and may be
  easily :ref:`disabled <disabling-ssh-config>` by advanced users seeking
  purity of state.
