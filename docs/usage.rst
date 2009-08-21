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

.. _combining-host-lists:

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
problem. Set ``env.disable_known_hosts`` to True when you want this behavior; it
is False by default, in order to preserve default SSH behavior.

.. warning::
    Enabling ``env.disable_known_hosts`` will leave you wide open to
    man-in-the-middle attacks! Please use with caution.


.. _output-controls:

Output controls
===============

The ``fab`` tool is very verbose by default and prints out almost everything it
can, including the remote end's stderr and stdout streams, the command strings
being executed, and so forth. While this is necessary in many cases in order to
know just what's going on, any nontrivial Fabric task will quickly become
difficult to follow as it runs.

To solve this problem, Fabric allows granular control over its output, which is
grouped into the following levels:

* **status**: Status messages, i.e. noting when Fabric is done running, if
  the user used a keyboard interrupt, or when servers are disconnected from.
  These messages are almost always necessary and rarely verbose.

* **aborts**: Abort messages. Like status messages, these should really only be
  turned off when using Fabric as a library, and possibly not even then. Note
  that even if this output group is turned off, aborts will still occur --
  there just won't be any output about why Fabric aborted!

* **warnings**: Warning messages. These are often turned off when one expects a
  given operation to fail, such as when using ``grep`` to test existence of
  text in a file. If paired with setting ``env.warn_only`` to True, this
  results in fully silent warnings when remote programs fail. As with
  ``aborts``, this setting does not control actual warning behavior, only
  whether warning messages are printed or hidden.

* **running**: Printouts of commands being executed or files transferred, e.g.
  ``[myserver] run: ls /var/www``.

* **stdout**: Local, or remote, stdout, i.e. non-error output from commands.

* **stderr**: Local, or remote, stderr, i.e. error-related output from commands.

* **debug**: Turn on debugging. Typically off; used to see e.g. the "full"
  commands being run (i.e. where before you would only see the command as
  passed to `run`, with debugging on you would see the full ``/bin/bash -l -c
  "<command>"`` string) as well as various other debug-type output. May add
  additional output, or modify pre-existing output.
    
  Where modifying other pieces of output (such as in the above example where it
  modifies the 'running' line to show the shell and any escape characters),
  this setting takes precedence over the others; so if ``running`` is False but
  ``debug`` is True, you will still be shown the 'running' line in its
  debugging form.

In addition to these granular levels, the following act as "aliases" for groups
of the above:

* **output**: Maps to both ``stdout`` and ``stderr``. Useful for when you only
  care to see the 'running' lines and your own print statements (and warnings).

* **everything**: Includes ``warnings``, ``running`` and ``output`` (see
  above.) Thus, when turning off ``everything``, you will only see a bare
  minimum of output, along with your own print statements.

You may toggle any and all of the above levels in a few ways:

* **Direct modification of fabric.state.output**: `fabric.state.output` is a
  dictionary subclass (similar to `fabric.state.env`) whose keys are the above
  levels, and whose value are either True or False. Naturally, a True value
  results in display of that output group, and False hides it.

* **Context managers**: `~fabric.context_managers.hide` and
  `~fabric.context_managers.show` are twin context managers that take one or
  more output level names as strings, and either hide or show them within the
  wrapped block. As with most other context managers, the prior values are
  restored when the block exits.

* **Command-line arguments**: You may pass ``--hide`` and/or ``--show``
  arguments to ``fab``, which behave exactly like the context managers of the
  same names (but are, naturally, globally applied) and take comma-separated
  strings as input.

All levels, save for ``debug``, are on by default.
