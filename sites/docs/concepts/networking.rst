==========
Networking
==========

.. _ssh-gateways:

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

There are two gateway solutions available in Fabric, mirroring the
functionality of OpenSSH's client: ``ProxyJump`` style (easier, less overhead,
can be nested) or ``ProxyCommand`` style (more overhead, can't be nested,
sometimes more flexible). Both support the usual range of configuration
sources: Fabric's own config framework, SSH config files, or runtime
parameters.

``ProxyJump``
-------------

This style of gateway uses the SSH protocol's ``direct-tcpip`` channel type - a
lightweight method of requesting that the gateway's ``sshd`` open a connection
on our behalf to another system. (This has been possible in OpenSSH server for
a long time; support in OpenSSH's client is new as of 7.3.)

Channel objects (instances of `paramiko.channel.Channel`) implement Python's
socket API and are thus usable in place of real operating system sockets for
nearly any Python code.

``ProxyJump`` style gatewaying is simple to use: create a new `.Connection`
object parameterized for the gateway, and supply it as the ``gateway``
parameter when creating your inner/real `.Connection`::

    from fabric import Connection

    c = Connection('internalhost', gateway=Connection('gatewayhost'))

As with any other `.Connection`, the gateway connection may be configured with
its own username, port number, and so forth. (This includes ``gateway`` itself
- they can be chained indefinitely!)

.. TODO:
    should it default to user/port from the 'outer' Connection? Some users may
    assume it will? (Probably most likely to assume user is preserved; port
    less so?)

``ProxyCommand``
----------------

The traditional OpenSSH command-line client has long offered a ``ProxyCommand``
directive (see `man ssh_config <http://man.openbsd.org/ssh_config>`_), which
pipes the inner connection's input and output through an arbitrary local
subprocess.

Compared to ``ProxyJump`` style gateways, this adds overhead (the extra
subprocess) and can't easily be nested. In trade, it allows for advanced tricks
like use of SOCKS proxies, or custom filtering/gatekeeping applications.

``ProxyCommand`` subprocesses are typically another ``ssh`` command, such as
``ssh -W %h:%p gatewayhost``; or (on SSH versions lacking ``-W``) the widely
available ``netcat``, via ``ssh gatewayhost nc %h %p``.

Fabric supports ``ProxyCommand`` by accepting command string objects in the
``gateway`` kwarg of `.Connection`; this is used to populate a
`paramiko.proxy.ProxyCommand` object at connection time.

Additional concerns
-------------------

If you're unsure which of the two approaches to use: use ``ProxyJump`` style.
It performs better, uses fewer resources on your local system, and has an
easier-to-use API.

.. warning::
    Requesting both types of gateways simultaneously to the same host (i.e.
    supplying a `.Connection` as the ``gateway`` via kwarg or config, *and*
    loading a config file containing ``ProxyCommand``) is considered an error
    and will result in an exception.
