Fabric is a Python (2.6+, 3.2+) library for high level, Pythonic SSH command
execution. It builds on top of `Invoke <http://pyinvoke.org>`_ (task and
command primitives) and `Paramiko <http://paramiko.org>`_ (SSH protocol
implementation), extending their APIs to complement one another & provide
additional functionality, all in a single consistent namespace.

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
    for host, result in results.items(): # 'results' is a dict
        print("{0} is {1}".format(host.name, result.stdout.strip()))

resulting in e.g.::

    web1 is Linux
    web2 is Darwin

Fabric also provides a task-oriented API, where you define a block of Python
functionality oriented around some generic target host, and allow client code
or command-line users to determine what host or hosts that task is executed on.
(This mode of behavior is similar to Fabric's primary API in versions prior to
2.0.)

For example, you might define a task function like so::

    from fabric import task

    @task
    def get_uname(host):
        result = host.run("uname -s")
        print("{0} is {1}".format(host.name, result.stdout.strip()))

and execute it like this::

    $ fab -H web1,web2 get_uname
    Running 'get_uname' on ['web1', 'web2']...
    web1 is Linux
    web2 is Darwin

    Done.
