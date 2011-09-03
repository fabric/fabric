===============
Execution model
===============

If you've read the :doc:`../tutorial`, you should already be familiar with how
Fabric operates in the base case (a single task on a single host.) However, in
many situations you'll find yourself wanting to execute multiple tasks and/or
on multiple hosts. Perhaps you want to split a big task into smaller reusable
parts, or crawl a collection of servers looking for an old user to remove. Such
a scenario requires specific rules for when and how tasks are executed.

This document explores Fabric's execution model, including the main execution
loop, how to define host lists, how connections are made, and so forth.

.. note::

    Most of this material applies to the :doc:`fab <fab>` tool only, as this
    mode of use has historically been the main focus of Fabric's development.
    When writing version 0.9 we straightened out Fabric's internals to make it
    easier to use as a library, but there's still work to be done before this
    is as flexible and easy as we'd like it to be.

.. _execution-strategy:

Execution strategy
==================

Fabric currently provides a single, serial execution method, though more
options are planned for the future:

* A list of tasks is created. Currently this list is simply the arguments given
  to :doc:`fab <fab>`, preserving the order given.
* For each task, a task-specific host list is generated from various
  sources (see :ref:`host-lists` below for details.)
* The task list is walked through in order, and each task is run once per host
  in its host list.
* Tasks with no hosts in their host list are considered local-only, and will
  always run once and only once.

Thus, given the following fabfile::

    from fabric.api import run, env

    env.hosts = ['host1', 'host2']

    def taskA():
        run('ls')

    def taskB():
        run('whoami')

and the following invocation::

    $ fab taskA taskB

you will see that Fabric performs the following:

* ``taskA`` executed on ``host1``
* ``taskA`` executed on ``host2``
* ``taskB`` executed on ``host1``
* ``taskB`` executed on ``host2``

While this approach is simplistic, it allows for a straightforward composition
of task functions, and (unlike tools which push the multi-host functionality
down to the individual function calls) enables shell script-like logic where
you may introspect the output or return code of a given command and decide what
to do next.

Defining tasks
==============

For details on what constitutes a Fabric task and how to organize them, please see :doc:`/usage/tasks`.

Defining host lists
===================

Unless you're using Fabric as a simple build system (which is possible, but not
the primary use-case) having tasks won't do you any good without the ability to
specify remote hosts on which to execute them. There are a number of ways to do
so, with scopes varying from global to per-task, and it's possible mix and
match as needed.

.. _host-strings:

Hosts
-----

Hosts, in this context, refer to what are also called "host strings": Python
strings specifying a username, hostname and port combination, in the form of
``username@hostname:port``. User and/or port (and the associated ``@`` or
``:``) may be omitted, and will be filled by the executing user's local
username, and/or port 22, respectively. Thus, ``admin@foo.com:222``,
``deploy@website`` and ``nameserver1`` could all be valid host strings.

.. note::
    The user/hostname split occurs at the last ``@`` found, so e.g. email
    address usernames are valid and will be parsed correctly.

During execution, Fabric normalizes the host strings given and then stores each
part (username/hostname/port) in the environment dictionary, for both its use
and for tasks to reference if the need arises. See :doc:`env` for details.

Roles
-----

Host strings map to single hosts, but sometimes it's useful to arrange hosts in
groups. Perhaps you have a number of Web servers behind a load balancer and
want to update all of them, or want to run a task on "all client servers".
Roles provide a way of defining strings which correspond to lists of host
strings, and can then be specified instead of writing out the entire list every
time.

This mapping is defined as a dictionary, ``env.roledefs``, which must be
modified by a fabfile in order to be used. A simple example::

    from fabric.api import env

    env.roledefs['webservers'] = ['www1', 'www2', 'www3']

Since ``env.roledefs`` is naturally empty by default, you may also opt to
re-assign to it without fear of losing any information (provided you aren't
loading other fabfiles which also modify it, of course)::

    from fabric.api import env

    env.roledefs = {
        'web': ['www1', 'www2', 'www3'],
        'dns': ['ns1', 'ns2']
    }

In addition to list/iterable object types, the values in ``env.roledefs`` may
be callables, and will thus be called when looked up when tasks are run instead
of at module load time. (For example, you could connect to remote servers
to obtain role definitions, and not worry about causing delays at fabfile load
time when calling e.g. ``fab --list``.)

Use of roles is not required in any way -- it's simply a convenience in
situations where you have common groupings of servers.

.. versionchanged:: 0.9.2
    Added ability to use callables as ``roledefs`` values.

.. _host-lists:

How host lists are constructed
------------------------------

There are a number of ways to specify host lists, either globally or per-task,
and generally these methods override one another instead of merging together
(though this may change in future releases.) Each such method is typically
split into two parts, one for hosts and one for roles.

Globally, via ``env``
~~~~~~~~~~~~~~~~~~~~~

The most common method of setting hosts or roles is by modifying two key-value
pairs in the environment dictionary, :doc:`env <env>`: ``hosts`` and ``roles``.
The value of these variables is checked at runtime, while constructing each
tasks's host list.

Thus, they may be set at module level, which will take effect when the fabfile
is imported::

    from fabric.api import env, run

    env.hosts = ['host1', 'host2']

    def mytask():
        run('ls /var/www')

Such a fabfile, run simply as ``fab mytask``, will run ``mytask`` on ``host1``
followed by ``host2``.

Since the env vars are checked for *each* task, this means that if you have the
need, you can actually modify ``env`` in one task and it will affect all
following tasks::

    from fabric.api import env, run

    def set_hosts():
        env.hosts = ['host1', 'host2']

    def mytask():
        run('ls /var/www')

When run as ``fab set_hosts mytask``, ``set_hosts`` is a "local" task -- its
own host list is empty -- but ``mytask`` will again run on the two hosts given.

.. note::

    This technique used to be a common way of creating fake "roles", but is
    less necessary now that roles are fully implemented. It may still be useful
    in some situations, however.

Alongside ``env.hosts`` is ``env.roles`` (not to be confused with
``env.roledefs``!) which, if given, will be taken as a list of role names to
look up in ``env.roledefs``.

Globally, via the command line
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to modifying ``env.hosts``, ``env.roles``, and
``env.exclude_hosts`` at the module level, you may define them by passing
comma-separated string arguments to the command-line switches
:option:`--hosts/-H <-H>` and :option:`--roles/-R <-R>`, e.g.::

    $ fab -H host1,host2 mytask

Such an invocation is directly equivalent to ``env.hosts = ['host1', 'host2']``
-- the argument parser knows to look for these arguments and will modify
``env`` at parse time.

.. note::

    It's possible, and in fact common, to use these switches to set only a
    single host or role. Fabric simply calls ``string.split(',')`` on the given
    string, so a string with no commas turns into a single-item list.

It is important to know that these command-line switches are interpreted
**before** your fabfile is loaded: any reassignment to ``env.hosts`` or
``env.roles`` in your fabfile will overwrite them.

If you wish to nondestructively merge the command-line hosts with your
fabfile-defined ones, make sure your fabfile uses ``env.hosts.extend()``
instead::

    from fabric.api import env, run

    env.hosts.extend(['host3', 'host4'])

    def mytask():
        run('ls /var/www')

When this fabfile is run as ``fab -H host1,host2 mytask``, ``env.hosts`` will
then contain ``['host1', 'host2', 'host3', 'host4']`` at the time that
``mytask`` is executed.

.. note::

    ``env.hosts`` is simply a Python list object -- so you may use
    ``env.hosts.append()`` or any other such method you wish.

.. _hosts-per-task-cli:

Per-task, via the command line
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Globally setting host lists only works if you want all your tasks to run on the
same host list all the time. This isn't always true, so Fabric provides a few
ways to be more granular and specify host lists which apply to a single task
only. The first of these uses task arguments.

As outlined in :doc:`fab`, it's possible to specify per-task arguments via a
special command-line syntax. In addition to naming actual arguments to your
task function, this may be used to set the ``host``, ``hosts``, ``role`` or
``roles`` "arguments", which are interpreted by Fabric when building host lists
(and removed from the arguments passed to the task itself.)

.. note::

    Since commas are already used to separate task arguments from one another,
    semicolons must be used in the ``hosts`` or ``roles`` arguments to
    delineate individual host strings or role names. Furthermore, the argument
    must be quoted to prevent your shell from interpreting the semicolons.

Take the below fabfile, which is the same one we've been using, but which
doesn't define any host info at all::

    from fabric.api import run

    def mytask():
        run('ls /var/www')

To specify per-task hosts for ``mytask``, execute it like so::

    $ fab mytask:hosts="host1;host2"

This will override any other host list and ensure ``mytask`` always runs on
just those two hosts.


Per-task, via decorators
~~~~~~~~~~~~~~~~~~~~~~~~

If a given task should always run on a predetermined host list, you may wish to
specify this in your fabfile itself. This can be done by decorating a task
function with the `~fabric.decorators.hosts` or `~fabric.decorators.roles`
decorators. These decorators take a variable argument list, like so::

    from fabric.api import hosts, run

    @hosts('host1', 'host2')
    def mytask():
        run('ls /var/www')

They will also take an single iterable argument, e.g.::

    my_hosts = ('host1', 'host2')
    @hosts(my_hosts)
    def mytask():
        # ...

When used, these decorators override any checks of ``env`` for that particular
task's host list (though ``env`` is not modified in any way -- it is simply
ignored.) Thus, even if the above fabfile had defined ``env.hosts`` or the call
to :doc:`fab <fab>` uses :option:`--hosts/-H <-H>`, ``mytask`` would still run
on a host list of ``['host1', 'host2']``.

However, decorator host lists do **not** override per-task command-line
arguments, as given in the previous section.


Order of precedence
~~~~~~~~~~~~~~~~~~~

We've been pointing out which methods of setting host lists trump the others,
as we've gone along. However, to make things clearer, here's a quick breakdown:

* Per-task, command-line host lists (``fab mytask:host=host1``) override
  absolutely everything else.
* Per-task, decorator-specified host lists (``@hosts('host1')``) override the
  ``env`` variables.
* Globally specified host lists set in the fabfile (``env.hosts = ['host1']``)
  *can* override such lists set on the command-line, but only if you're not
  careful (or want them to.)
* Globally specified host lists set on the command-line (``--hosts=host1``)
  will initialize the ``env`` variables, but that's it.

This logic may change slightly in the future to be more consistent (e.g.
having :option:`--hosts <-H>` somehow take precedence over ``env.hosts`` in the
same way that command-line per-task lists trump in-code ones) but only in a
backwards-incompatible release.

.. _combining-host-lists:

Combining host lists
--------------------

There is no "unionizing" of hosts between the various sources mentioned in
:ref:`host-lists`. If ``env.hosts`` is set to ``['host1', 'host2', 'host3']``,
and a per-function (e.g.  via `~fabric.decorators.hosts`) host list is set to
just ``['host2', 'host3']``, that function will **not** execute on ``host1``,
because the per-task decorator host list takes precedence.

However, for each given source, if both roles **and** hosts are specified, they
will be merged together into a single host list. Take, for example, this
fabfile where both of the decorators are used::

    from fabric.api import env, hosts, roles, run

    env.roledefs = {'role1': ['b', 'c']}

    @hosts('a', 'b')
    @roles('role1')
    def mytask():
        run('ls /var/www')

Assuming no command-line hosts or roles are given when ``mytask`` is executed,
this fabfile will call ``mytask`` on a host list of ``['a', 'b', 'c']`` -- the
union of ``role1`` and the contents of the `~fabric.decorators.hosts` call.

.. _excluding-hosts:

Excluding specific hosts
------------------------

At times, it is useful to exclude one or more specific hosts, e.g. to override
a few bad or otherwise undesirable hosts which are pulled in from a role or an
autogenerated host list. This may be accomplished globally with
:option:`--exclude-hosts/-x <-x>`::

    $ fab -R myrole -x host2,host5 mytask

If ``myrole`` was defined as ``['host1', 'host2', ..., 'host15']``, the above
invocation would run with an effective host list of ``['host1', 'host3',
'host4', 'host6', ..., 'host15']``.

    .. note::
        Using this option does not modify ``env.hosts`` -- it only causes the
        main execution loop to skip the requested hosts.

Exclusions may be specified per-task by using an extra ``exclude_hosts`` kwarg,
which is implemented similarly to the abovementioned ``hosts`` and ``roles``
per-task kwargs, in that it is stripped from the actual task invocation. This
example would have the same result as the global exclude above::

    $ fab mytask:roles=myrole,exclude_hosts="host2;host5"

Note that the host list is semicolon-separated, just as with the ``hosts``
per-task argument.

Combining exclusions
~~~~~~~~~~~~~~~~~~~~

Host exclusion lists, like host lists themselves, are not merged together
across the different "levels" they can be declared in. For example, a global
``-x`` option will not affect a per-task host list set with a decorator or
keyword argument, nor will per-task ``exclude_hosts`` keyword arguments affect
a global ``-H`` list.

There is one minor exception to this rule, namely that CLI-level keyword
arguments (``mytask:exclude_hosts=x,y``) **will** be taken into account when
examining host lists set via ``@hosts`` or ``@roles``. Thus a task function
decorated with ``@hosts('host1', 'host2')`` executed as ``fab
taskname:exclude_hosts=host2`` will only run on ``host1``.

As with the host list merging, this functionality is currently limited (partly
to keep the implementation simple) and may be expanded in future releases.


.. _failures:

Failure handling
================

Once the task list has been constructed, Fabric will start executing them as
outlined in :ref:`execution-strategy`, until all tasks have been run on the
entirety of their host lists. However, Fabric defaults to a "fail-fast"
behavior pattern: if anything goes wrong, such as a remote program returning a
nonzero return value or your fabfile's Python code encountering an exception,
execution will halt immediately.

This is typically the desired behavior, but there are many exceptions to the
rule, so Fabric provides ``env.warn_only``, a Boolean setting. It defaults to
``False``, meaning an error condition will result in the program aborting
immediately. However, if ``env.warn_only`` is set to ``True`` at the time of
failure -- with, say, the `~fabric.context_managers.settings` context
manager -- Fabric will emit a warning message but continue executing.

.. _connections:

Connections
===========

``fab`` itself doesn't actually make any connections to remote hosts. Instead,
it simply ensures that for each distinct run of a task on one of its hosts, the
env var ``env.host_string`` is set to the right value. Users wanting to
leverage Fabric as a library may do so manually to achieve similar effects.

``env.host_string`` is (as the name implies) the "current" host string, and is
what Fabric uses to determine what connections to make (or re-use) when
network-aware functions are run. Operations like `~fabric.operations.run` or
`~fabric.operations.put` use ``env.host_string`` as a lookup key in a shared
dictionary which maps host strings to SSH connection objects.

.. note::

    The connections dictionary (currently located at
    ``fabric.state.connections``) acts as a cache, opting to return previously
    created connections if possible in order to save some overhead, and
    creating new ones otherwise.


Lazy connections
----------------

Because connections are driven by the individual operations, Fabric will not
actually make connections until they're necessary. Take for example this task
which does some local housekeeping prior to interacting with the remote
server::

    from fabric.api import *

    @hosts('host1')
    def clean_and_upload():
        local('find assets/ -name "*.DS_Store" -exec rm '{}' \;')
        local('tar czf /tmp/assets.tgz assets/')
        put('/tmp/assets.tgz', '/tmp/assets.tgz')
        with cd('/var/www/myapp/'):
            run('tar xzf /tmp/assets.tgz')

What happens, connection-wise, is as follows:

#. The two `~fabric.operations.local` calls will run without making any network
   connections whatsoever;
#. `~fabric.operations.put` asks the connection cache for a connection to
   ``host1``;
#. The connection cache fails to find an existing connection for that host
   string, and so creates a new SSH connection, returning it to
   `~fabric.operations.put`;
#. `~fabric.operations.put` uploads the file through that connection;
#. Finally, the `~fabric.operations.run` call asks the cache for a connection
   to that same host string, and is given the existing, cached connection for
   its own use.

Extrapolating from this, you can also see that tasks which don't use any
network-borne operations will never actually initiate any connections (though
they will still be run once for each host in their host list, if any.)

Closing connections
-------------------

Fabric's connection cache never closes connections itself -- it leaves this up
to whatever is using it. The :doc:`fab <fab>` tool does this bookkeeping for
you: it iterates over all open connections and closes them just before it exits
(regardless of whether the tasks failed or not.)

Library users will need to ensure they explicitly close all open connections
before their program exits. This can be accomplished by calling
`~fabric.network.disconnect_all` at the end of your script.

.. note::

    `~fabric.network.disconnect_all` may be moved to a more public location in
    the future; we're still working on making the library aspects of Fabric
    more solidified and organized.


.. _password-management:

Password management
===================

Fabric maintains an in-memory, two-tier password cache to help remember your
login and sudo passwords in certain situations; this helps avoid tedious
re-entry when multiple systems share the same password [#]_, or if a remote
system's ``sudo`` configuration doesn't do its own caching.

The first layer is a simple default or fallback password cache,
:ref:`env.password <password>`. This env var stores a single password which (if
non-empty) will be tried in the event that the host-specific cache (see below)
has no entry for the current :ref:`host string <host_string>`.

:ref:`env.passwords <passwords>` (plural!) serves as a per-user/per-host cache,
storing the most recently entered password for every unique user/host/port
combination.  Due to this cache, connections to multiple different users and/or
hosts in the same session will only require a single password entry for each.
(Previous versions of Fabric used only the single, default password cache and
thus required password re-entry every time the previously entered password
became invalid.)

Depending on your configuration and the number of hosts your session will
connect to, you may find setting either or both of these env vars to be useful.
However, Fabric will automatically fill them in as necessary without any
additional configuration.

Specifically, each time a password prompt is presented to the user, the value
entered is used to update both the single default password cache, and the cache
value for the current value of ``env.host_string``.

.. [#] We highly recommend the use of SSH `key-based access
    <http://en.wikipedia.org/wiki/Public_key>`_ instead of relying on
    homogeneous password setups, as it's significantly more secure.
