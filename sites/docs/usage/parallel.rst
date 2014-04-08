==================
Parallel execution
==================

.. versionadded:: 1.3

By default, Fabric executes all specified tasks **serially** (see
:ref:`execution-strategy` for details.) This document describes Fabric's
options for running tasks on multiple hosts in **parallel**, via per-task
decorators and/or global command-line switches.


What it does
============

Because Fabric 1.x is not fully threadsafe (and because in general use, task
functions do not typically interact with one another) this functionality is
implemented via the Python `multiprocessing
<http://docs.python.org/library/multiprocessing.html>`_ module. It creates one
new process for each host and task combination, optionally using a
(configurable) sliding window to prevent too many processes from running at the
same time.

For example, imagine a scenario where you want to update Web application code
on a number of Web servers, and then reload the servers once the code has been
distributed everywhere (to allow for easier rollback if code updates fail.) One
could implement this with the following fabfile::

    from fabric.api import *

    def update():
        with cd("/srv/django/myapp"):
            run("git pull")

    def reload():
        sudo("service apache2 reload")

and execute it on a set of 3 servers, in serial, like so::

    $ fab -H web1,web2,web3 update reload

Normally, without any parallel execution options activated, Fabric would run
in order:

#. ``update`` on ``web1``
#. ``update`` on ``web2``
#. ``update`` on ``web3``
#. ``reload`` on ``web1``
#. ``reload`` on ``web2``
#. ``reload`` on ``web3``

With parallel execution activated (via :option:`-P` -- see below for details),
this turns into:

#. ``update`` on ``web1``, ``web2``, and ``web3``
#. ``reload`` on ``web1``, ``web2``, and ``web3``

Hopefully the benefits of this are obvious -- if ``update`` took 5 seconds to
run and ``reload`` took 2 seconds, serial execution takes (5+2)*3 = 21 seconds
to run, while parallel execution takes only a third of the time, (5+2) = 7
seconds on average.


How to use it
=============

Decorators
----------

Since the minimum "unit" that parallel execution affects is a task, the
functionality may be enabled or disabled on a task-by-task basis using the
`~fabric.decorators.parallel` and `~fabric.decorators.serial` decorators. For
example, this fabfile::

    from fabric.api import *

    @parallel
    def runs_in_parallel():
        pass

    def runs_serially():
        pass

when run in this manner::

    $ fab -H host1,host2,host3 runs_in_parallel runs_serially

will result in the following execution sequence:

#. ``runs_in_parallel`` on ``host1``, ``host2``, and ``host3``
#. ``runs_serially`` on ``host1``
#. ``runs_serially`` on ``host2``
#. ``runs_serially`` on ``host3``

Command-line flags
------------------

One may also force all tasks to run in parallel by using the command-line flag
:option:`-P` or the env variable :ref:`env.parallel <env-parallel>`.  However,
any task specifically wrapped with `~fabric.decorators.serial` will ignore this
setting and continue to run serially.

For example, the following fabfile will result in the same execution sequence
as the one above::

    from fabric.api import *

    def runs_in_parallel():
        pass

    @serial
    def runs_serially():
        pass

when invoked like so::

    $ fab -H host1,host2,host3 -P runs_in_parallel runs_serially

As before, ``runs_in_parallel`` will run in parallel, and ``runs_serially`` in
sequence.


Bubble size
===========

With large host lists, a user's local machine can get overwhelmed by running
too many concurrent Fabric processes. Because of this, you may opt to use a
moving bubble approach that limits Fabric to a specific number of concurrently
active processes.

By default, no bubble is used and all hosts are run in one concurrent pool. You
can override this on a per-task level by specifying the ``pool_size`` keyword
argument to `~fabric.decorators.parallel`, or globally via :option:`-z`.

For example, to run on 5 hosts at a time::

    from fabric.api import *

    @parallel(pool_size=5)
    def heavy_task():
        # lots of heavy local lifting or lots of IO here

Or skip the ``pool_size`` kwarg and instead::

    $ fab -P -z 5 heavy_task

.. _linewise-output:

Linewise vs bytewise output
===========================

Fabric's default mode of printing to the terminal is byte-by-byte, in order to
support :doc:`/usage/interactivity`. This often gives poor results when running
in parallel mode, as the multiple processes may write to your terminal's
standard out stream simultaneously.

To help offset this problem, Fabric's option for linewise output is
automatically enabled whenever parallelism is active. This will cause you to
lose most of the benefits outlined in the above link Fabric's remote
interactivity features, but as those do not map well to parallel invocations,
it's typically a fair trade.

There's no way to avoid the multiple processes mixing up on a line-by-line
basis, but you will at least be able to tell them apart by the host-string line
prefix.

.. note::
    Future versions will add improved logging support to make troubleshooting
    parallel runs easier.
