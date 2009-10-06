============================
Executing tasks with ``fab``
============================

* Don't need to call connection.close() like in the tutorial -- ``fab`` it does
  it for you



Each command/task name mentioned on the command line is executed once per host
in the host list for that command. If no hosts are found for a given command,
by using the below lookup strategy, it is considered local-only and will simply
run once.


Multiple tasks and/or hosts
---------------------------

There are often situations where executing multiple tasks or connecting to
multiple hosts becomes useful. Fabric follows a relatively simple serial
pattern when it comes to executing multiple tasks via the ``fab`` tool:

* Tasks are executed in the order given on the command line;
* Each task is executed once per host in that task's host list.

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

This allows for a straightforward composition of task functions, as they will
run against a single host at a time -- enabling shell script-like logic where
you may introspect the stdout or stderr of a given command and decide what to
do next.

See :doc:`execution` for more details and background on this topic.

Which functions are tasks?
--------------------------

When looking for tasks to execute, Fabric will consider any callable:

* whose name doesn't start with an underscore (``_``). In other words, Python's
  usual "private" convention holds true here.
* which isn't defined within Fabric itself. Therefore, Fabric's own functions
  such as `~fabric.operations.run` and `~fabric.operations.sudo`  will not show
  up in your task list.

To see exactly which callables in your fabfile may be executed via ``fab``,
use ``fab --list``. For some additional notes concerning task discovery and
fabfile loading, see :doc:`execution`.



Importing other modules
=======================

Because of the way the ``fab`` tool runs, any callables found in your fabfile
will be candidates for execution, displayed in ``fab --list``, and so forth.
This can lead to minor annoyances if your fabfile contains ``from module import
callable``-style imports -- all such callables will appear in ``fab --list``,
cluttering it up. Because of this, we strongly recommend that you use ``import
module`` followed by ``module.callable()`` in order to give your fabfile a
clean API.

.. note::
    Fabric strips out its own callables when building the list of potential
    commands, so you don't need to worry about finding ``run`` or ``sudo`` in
    your ``--list`` output.

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



Failure handling
----------------

As we mentioned earlier during the introduction of the
`~fabric.context_managers.settings` context manager, Fabric defaults to a
"fail-fast" behavior pattern: if anything goes wrong, such as a remote program
returning a nonzero return value, execution will halt immediately.

This is typically the desired behavior, but there are many exceptions to the
rule, so Fabric provides a ``warn_only`` Boolean setting. If ``warn_only`` is
set to True at the time of failure, Fabric will emit a warning message but
continue executing.
