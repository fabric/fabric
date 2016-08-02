==========
Networking
==========

SSH connection gateways
=======================

Background
----------

When connecting to well-secured networks whose internal hosts are not directly
reachable from the Internet, a common pattern is "bouncing", "gatewaying" or
"proxying" SSH connections via an intermediate host (often called a "bastion",
"gateway" or "jump box").

Gatewaying requires making an initial/outer SSH connection to the gateway
system, then using that connection as a transport for the "real"
connection to the final/internal host.

At a basic level, one could ``ssh gatewayhost``, then ``ssh internalhost`` from
the resulting shell. This works for individual long-running sessions, but
becomes a burden when it must be done frequently.

There are two gateway solutions available in Fabric: ``direct-tcpip`` (easier,
less overhead) or ``ProxyCommand`` (more overhead, only reads your SSH config
and not any Fabric-level config, but sometimes more flexible).

``direct-tcpip``
----------------

This style of gateway is so named because it uses the SSH protocol's
``direct-tcpip`` channel type - a lightweight method of requesting that the
gateway's ``sshd`` open a connection on our behalf to an internal system.

Its implementation in Fabric is simple: just create a new `.Connection` object
parameterized for the gateway, and use it as the ``gateway`` parameter when
creating your inner/real `.Connection`::

    from fabric import Connection

    cxn = Connection('internalhost', gateway=Connection('gatewayhost'))

``ProxyCommand``
----------------

The traditional OpenSSH command-line client offers a ``ProxyCommand`` directive
(see `man ssh_config <http://man.openbsd.org/ssh_config>`_), which pipes the
inner connection's input and output through an arbitrary local subprocess.

Compared to ``direct-tcpip`` gateways, this adds overhead (the extra
subprocess) and requires that all pertinent connection parameters live in
your OpenSSH config file (as opposed to anything read via Fabric's own
configuration system). In trade, it allows for advanced tricks, such as SSH
port forwarding / tunnelling, use of SOCKS proxies, or custom
filtering/gatekeeping applications.

``ProxyCommand`` subprocesses are typically another ``ssh`` command, such as
``ssh -W %h:%p gatewayhost``; or (on SSH versions lacking ``-W``) the widely
available ``netcat``, via ``nc %h %p``.

If Fabric detects an applicable ``ProxyCommand`` directive in a loaded SSH
config file, it will be used automatically.

.. TODO:: expand this when 'in-memory' ssh_config manipulation becomes a thing

Additional concerns
-------------------

If you're unsure which of the two approaches to use: use ``direct-tcpip``. It
performs better, uses fewer resources on your local system, and has an
easier-to-use API.

.. warning::
    It's not possible to activate both styles of gateway for the same
    connection. If Fabric sees a non-empty ``gateway`` kwarg *and* a configured
    ``ProxyCommand``, it will exit with a complaint.


other sections TK... (maybe nest files further??):

- connection handling / lazy connecting / closing connections / etc (possibly
  less critical now that connections have a more explicit lifecycle?)
- Skipping various kinds of 'bad' hosts
- Timeouts
- Reconnection attempts
- Parallel connections
- Look in fab 1 docs for more that we can already easily support
- keepalives? other new things?
- Should SSH host tracking live here or under 'ssh' or 'security' type section?
