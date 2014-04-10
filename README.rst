Fabric is a Python (2.6+, 3.3+) library for high level, Pythonic SSH
command execution. It builds on top of `Invoke
<http://pyinvoke.org>`_ (task and command primitives) and `Paramiko
<http://paramiko.org>`_ (SSH protocol implementation), extending their APIs to
complement one another & provide additional functionality, all in a single
consistent namespace.

The most basic use of Fabric is to execute shell commands on one or more remote
servers. A single-server execution might look like this::

    from fabric import Host

    result = Host('web1.example.com').run('uname -s')
    print("web1 is {0}".format(result.stdout.strip()))

which could result in::

    web1 is Linux

To check the ``uname`` of multiple servers, you might do this::

    from fabric import HostCollection

    results = HostCollection('web1', 'web2').run('uname -s')
    for host, result in results.items():
        print("{0} is {1}".format(host.name, result.stdout.strip()))

Fabric also provides a task-oriented API, where you define Python functionality
oriented around a target host, and allow client code or command-line users to
determine what host or hosts that task is executed on. (This mode of behavior
is similar to Fabric's primary API in versions prior to 2.0.)
