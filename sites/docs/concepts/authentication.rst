==============
Authentication
==============

Even in the 'vanilla' OpenSSH client, authenticating to remote servers involves
multiple potential sources for secrets and configuration; Fabric not only
supports most of those, but has more of its own. This document outlines the
available methods for setting authentication secrets.

.. note::
    Since Fabric itself tries not to reinvent too much Paramiko functionality,
    most of the time configuring authentication values boils down to "how to
    set keyword argument values for `SSHClient.connect
    <paramiko.client.SSHClient.connect>`", which in turn means to set values
    inside either the ``connect_kwargs`` :doc:`config
    </concepts/configuration>` subtree, or the ``connect_kwargs`` keyword
    argument of `.Connection`.

Private key files
=================

Private keys stored on-disk are probably the most common auth mechanism for
SSH. Fabric offers multiple methods of configuring which paths to use, most of
which end up merged into one list of paths handed to
``SSHClient.connect(key_filename=[...])``, in the following order:

- If a ``key_filename`` key exists in the ``connect_kwargs`` argument to
  `.Connection`, they come first in the list. (This is basically the "runtime"
  option for non-CLI users.)
- The config setting ``connect_kwargs.key_filename`` can be set in a number of
  ways (as per the :doc:`config docs </concepts/configuration>`) including via
  the :option:`--identity` CLI flag (which sets the ``overrides`` level of the
  config; so when this flag is used, key filename values from other config
  sources will be overridden.) This value comes next in the overall list.
- Using an :ref:`ssh_config <ssh-config>` file with ``IdentityFile``
  directives lets you share configuration with other SSH clients; such values
  come last.

Encryption passphrases
----------------------

If your private key file is protected via a passphrase, it can be supplied in a
handful of ways:

- The ``connect_kwargs.passphrase`` config option is the most direct way to
  supply a passphrase to be used automatically.

  .. note::
    Using actual on-disk config files for this type of material isn't always
    wise, but recall that the :doc:`configuration system
    </concepts/configuration>` is capable of loading data from other sources,
    such as your shell environment or even arbitrary remote databases.

- If you prefer to enter the passphrase manually at runtime, you may use the
  command-line option :option:`--prompt-for-passphrase`, which will cause
  Fabric to interactively prompt the user at the start of the process, and
  store the entered value in ``connect_kwargs.passphrase`` (at the 'overrides'
  level.)

Private key objects
===================

Instantiate your own `PKey <paramiko.pkey.PKey>` object (see its subclasses'
API docs for details) and place it into ``connect_kwargs.pkey``. That's it!
You'll be responsible for any handling of passphrases, if the key material
you're loading (these classes can load from file paths or strings) is
encrypted.

SSH agents
==========

By default (similar to how OpenSSH behaves) Paramiko will attempt to connect to
a running SSH agent (Unix style, e.g. a live ``SSH_AUTH_SOCK``, or Pageant if
one is on Windows). This can be disabled by setting
``connect_kwargs.allow_agent`` to ``False``.

Passwords
=========

Password authentication is relatively straightforward:

- You can configure it via ``connect_kwargs.password`` directly.
- If you want to be prompted for it at the start of a session, specify
  :option:`--prompt-for-login-password`.

.. TODO: host-configuration hooks are very important here, when implemented

GSSAPI
======

Fabric doesn't provide any extra GSSAPI support on top of Paramiko's existing
connect-time parameters (see e.g. ``gss_kex``/``gss_auth``/``gss_host``/etc in
`SSHClient.connect <paramiko.client.SSHClient.connect>`) and the modules
implementing the functionality itself (such as `paramiko.ssh_gss`.) Thus, as
usual, you should be looking to modify the ``connect_kwargs`` configuration
tree.
