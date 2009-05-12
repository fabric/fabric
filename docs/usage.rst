=================
How to use Fabric
=================

Importing Fabric itself
=======================

Simplest method, which is not PEP8-compliant (meaning it's not best practices)::

    from fabric.api import *

Slightly better, albeit verbose, method which *is* PEP8-compliant::

    from fabric.api import run, sudo, prompt, abort, ...

.. note::
    You can also import directly from the individual submodules, e.g.
    ``from fabric.utils import abort``. However, all of Fabric's public API is
    guaranteed to be available via `fabric.api` for convenience purposes.


Importing other modules
=======================

Because of the way the ``fab`` tool runs, any callables found in your fabfile
(excepting Fabric's own callables, which it filters out) will be candidates for
execution, and will be displayed in ``fab --list``, and so forth.

This can lead to minor annoyances if you do a lot of ``from module import
callable``-style imports in your fabfile. Thus, we strongly recommend that you
use ``import module`` followed by ``module.callable()`` in order to give your
fabfile a clean API.

Rationale
---------

Take the following example where we need to use ``urllib.urlopen`` to get some
data out of a webservice::

    from urllib import urlopen

    from fabric.api import run

    def my_task():
        """
        List some directories.
        """
        directories = urlopen('http://my/web/service/?foo=bar').read().split()
        for directory in directories:
            run('ls %s' % directory)

This looks simple enough, and will run without error. However, look what
happens if we run ``fab --list`` on this fabfile::

    $ fab --list
    Available commands:

      my_task    List some directories.   
      urlopen    urlopen(url [, data]) -> open file-like object

Our fabfile of only one task is showing two "tasks", which is bad enough, and
an unsuspecting user might accidentally try to call ``fab urlopen``, which
probably won't work too well. Imagine any real-world fabfile, which is likely
to be much more complex, and hopefully you can see how this could get messy
fast.


.. _execution-model:

Execution model
===============

Each command/task name mentioned on the command line is executed once per host
in the host list for that command. If no hosts are found for a given command,
by using the below lookup strategy, it is considered local-only and will simply
run once.

Defining hosts
----------------

Hosts, in this context, refer to what are also called "host strings": Python
strings referring to a specific user, hostname and port combination, in the
format ``user@hostname:port``. User and/or port (and the associated ``@`` or
``:``) may be omitted, and will be filled by the executing user's local
username, and/or port 22, respectively.

Thus, ``admin@foo.com:222``, ``deploy@website`` and ``nameserver1`` could all
be valid host strings.

Defining roles
----------------

Roles are simply string identifiers mapping to lists of host strings. This
mapping is defined as a dictionary, ``env.roledefs``, and must be modified by a
fabfile in order to be referenced, e.g.::

    from fabric.api import env

    env.roledefs['webservers'] = ['www1', 'www2', 'www3']

Since this dictionary is naturally empty by default, you may also opt to
re-assign to it without fear of losing any information (provided you aren't
loading other fabfiles which also modify it, of course)::

    from fabric.api import env

    env.roledefs = {
        'web': ['www1', 'www2', 'www3'],
        'dns': ['ns1', 'ns2']
    }


How host lists are constructed
------------------------------

Construction of a command's host list follows a strict order of precedence, so
that the first available set of hosts in the list wins and the rest of the
checks are skipped. Hosts and roles may be specified simultaneously and will be
combined; see :ref:`combining-host-lists` for details.

The lookup order is as follows:

#. Per-command hosts or roles specified via the command line (e.g. ``fab
   foo:hosts='a;b;c'``)
#. Hosts specified via the `~fabric.decorators.hosts` and
   `~fabric.decorators.roles` decorators
#. The values of ``env.hosts`` and/or ``env.roles`` (both being lists of
   strings, host strings or role names respectively) which may be set via:

    * The command-line options ``--hosts`` and ``--roles`` (using
      comma-separated lists of strings)
    * Python code operating on ``env`` within your fabfile (which will append
      to or overwrite anything set on the command line)

    Note that you may set either of these at module level, in which case the
    given list will apply globally to all commands (unless overridden in one of
    the previous ways.)

Using env vars and shared state to create "environments"
--------------------------------------------------------

Because env vars, including ``env.hosts`` and ``env.roles``, are shared between
commands, you may update these lists inside one command and they will affect
this host lookup process for any commands that run after it. A useful trick is
to take advantage of this in order to have one (local-only) command modify the
environment for remote commands.

Here's a sample fabfile illustrating this tactic::

    def staging():
        env.hosts = ['staging-server']
        env.user = 'deploy'

    def production():
        env.hosts = ['prod-server']
        env.user = 'deploy2'

    def deploy():
        run('foo')
        sudo('bar')

One would use the above fabfile like so::

    $ fab staging deploy

Because ``env.hosts`` is set in the ``staging`` command and is not otherwise
defined, the ``deploy`` command will inherit the host list
``['staging-server']``.

.. note::
    This functionality is likely to become solidified into something less
    ad-hoc in the near future, so keep an eye out!

.. _combining-host-lists::

Combining host lists
--------------------

There is no "unionizing" of hosts between the various sources mentioned above.
If a global host list contains hosts A, B and C, and a per-function (e.g.
via `~fabric.decorators.hosts`) host list is set to just hosts B and C, that
function will **not** execute on host A.

However, `~fabric.decorators.hosts` and `~fabric.decorators.roles` **will**
result in the union of their contents as the final host list. In the following
example, the resulting host list will be ``['a', 'b', 'c']``::


    env.roledefs = {'role1': ['b', 'c']}

    @hosts('a', 'b')
    @roles('role1')
    def my_func():
        pass


SSH behavior
============

Fabric currently makes use of the `Paramiko
<http://www.lag.net/paramiko/docs/>`_ SSH library for managing all connections,
meaning that there are occasionally spots where it is limited by Paramiko's
capabilities. Below are areas of note where Fabric will exhibit behavior that
isn't consistent with, or as flexible as, the behavior of the ``ssh`` program.

Unknown hosts
-------------
SSH's host key tracking mechanism keeps tabs on all the hosts you attempt to
connect to, and maintains a ``~/.ssh/known_hosts`` file with mappings between
identifiers (IP address, sometimes with a hostname as well) and SSH keys. (For
details on how this works, please see the `OpenSSH documentation
<http://openssh.org/manual.html>`_.)

Paramiko is capable of loading up your ``known_hosts`` file, and will then
compare any host it connects to, with that mapping. Settings are available to
determine what happens when an unknown host (a host whose username or IP is not
found in ``known_hosts``) is seen:

* **Reject**: the host key is rejected and the connection is not made. This
  results in a Python exception, which will terminate your Fabric session with a
  message that the host is unknown.
* **Add**: the new host key is added to the in-memory list of known hosts, the
  connection is made, and things continue normally. Note that this does **not**
  modify your on-disk ``known_hosts`` file!
* **Ask**: not yet implemented at the Fabric level, this is a Paramiko option
  which would result in the user being prompted about this key and whether to
  accept it.

Whether to reject or add hosts, as above, is controlled in Fabric via the
``env.reject_unknown_hosts`` option, which is False by default for
convenience's sake.

Known hosts with changed keys
-----------------------------

The point of SSH's key tracking is so that man-in-the-middle attacks can be
detected: if an attacker redirects your SSH traffic to a computer under his
control, and pretends to be your original destination server, the host keys will
differ. Thus, the default behavior of SSH -- and Paramiko -- is to immediately
abort the connection when a host previously recorded in ``known_hosts`` suddenly
starts sending us a different host key.

In some edge cases such as some EC2 deployments, you may want to ignore this
potential problem. Paramiko, at the time of writing, doesn't give us control
over this behavior, but we can sidestep it by simply skipping the loading of
``known_hosts`` -- if the host list being compared to is empty, then there's no
problem. Set ``env.load_known_hosts`` to False when you want this behavior; it
is True by default, in order to preserve default SSH behavior.

.. warning::
    Disabling ``env.load_known_hosts`` will leave you wide open to
    man-in-the-middle attacks! Please use with caution.
