=====================
Overview and Tutorial
=====================

This document provides a high level overview of how to use Fabric, starting
with basic concepts and moving through progressively more complex (and
realistic!) example code. It tries to leave in-depth explanations to the rest
of the documentation, which is linked to in a number of places.

You will need Fabric :doc:`installed <installation>` in order to follow along.


.. _introduction:

Introduction
============

At its heart, Fabric can do two things:

* Execute (on the command line) arbitrary Python functions
* Execute (on remote servers) arbitrary shell commands

We'll tackle these in order, and then see how to use them together.

Python functions executed via the CLI
-------------------------------------

Fabric comes with a ``fab`` command-line tool capable of loading a Python
module (named ``fabfile`` by default and usually referred to as "a fabfile")
and executing functions defined within. Functions designed for use with
Fabric are referred to as "tasks" or "commands", and are pure Python code.

Let's start with a typical Hello World example. Create a ``fabfile.py`` in your
current directory and enter the following (and only the following: no imports
are necessary at this point)::

    def hello():
        print("Hello, world!")

Once you've saved this fabfile, you can execute the ``hello`` task with the
``fab`` command-line tool::

    $ fab hello
    Hello, world!

    Done.

That's all there is to it: define one or more tasks, then ask ``fab`` to
execute them. You may specify multiple task names, space-separated; for details
on ``fab``'s behavior and its options/arguments, please see :doc:`fab`.

Since a fabfile is simply a Python module, the sky's the limit. However, most
of the time you'll be interested in importing and using the other side of
Fabric: its SSH functionality.

Shell commands executed via SSH
-------------------------------

Fabric provides a number of API functions (sometimes referred to as
"operations") including two core functions which connect to remote servers
and execute their arguments as shell commands. These are roughly equivalent to
using the command-line SSH tool with extra arguments, e.g.::

  $ ssh myserver sudo /etc/init.d/apache2 reload

Use of this SSH API is relatively simple: just set an :ref:`environment
variable <environment>` telling Fabric what server to talk to, and call your
desired function. The most basic such function is `~fabric.operations.run`,
which calls a shell with the given command and returns the command's output
(printing out what it's doing all the while.) Here's an interactive Python
session making use of `~fabric.operations.run`::

    $ python
    >>> from fabric.api import run, env
    >>> from fabric.state import connections
    >>> env.host_string = "localhost"
    >>> result = run("ls")
    [localhost] run: ls
    [localhost] out: Desktop
    [localhost] out: Documents
    [localhost] out: Downloads
    [localhost] out: Dropbox
    [localhost] out: Library
    [localhost] out: Movies
    [localhost] out: Music
    [localhost] out: Pictures
    [localhost] out: Public
    [localhost] out: Sites
    [localhost] out: bin
    >>> connections["localhost"].close()
    >>> ^D
    $ 

Since we ran this against our local machine (and because Fabric uses your local
username as the username to connect with, by default -- see :ref:`foo` for
more), it printed out the contents of our home directory. Your results are
therefore likely to differ.

.. note::

    If you're following along, you'll want to replace ``"localhost"`` with the
    hostname of a computer you have SSH access to. If you're on a Linux or Mac
    machine, you may already have an SSH server running locally, as we do --
    it's certainly the easiest way to try out Fabric.

.. note::

    The use of the ``connections`` object to close the connection is necessary
    in order to cleanly exit the Python interpreter; otherwise your session
    will hang when you try to use Control-D or ``exit()``. This is less than
    ideal, and Fabric's usability as a library is expected to improve in
    version 1.0.

Putting it together
---------------------

While these two primary features of Fabric can be used separately, the main use
case is to combine them, defining and running (via ``fab``) task functions
which in turn import and use Fabric's API calls such as
`~fabric.operations.run`. Most of Fabric's auxiliary functions and tools
revolve around this mode of use.

Here's an example which simply takes the previous interactive example and drops
it into a fabfile::

    from fabric.api import run, env

    def list_home():
        env.host_string = 'localhost'
        result = run('ls')

.. note::

    When using functions like `~fabric.operations.run` in ``fab``-driven
    fabfiles, you don't need to bother with the ``connections`` object -- it's
    handled for you by ``fab``'s main execution loop. See :ref:`execution` for
    more on how the ``fab`` tool handles host connections.

The result is much the same as before::

    $ fab list_home

    [localhost] run: ls
    [localhost] out: Desktop
    [localhost] out: Documents
    [localhost] out: Downloads
    [localhost] out: Dropbox
    [localhost] out: Library
    [localhost] out: Movies
    [localhost] out: Music
    [localhost] out: Pictures
    [localhost] out: Public
    [localhost] out: Sites
    [localhost] out: bin

    Done.
    Disconnecting from localhost... done.

From here on, we'll be exploring the rest of Fabric's API and the various nuts
and bolts you'll need to understand in order to use Fabric effectively.


Operations
==========

In this section we'll give a quick tour of Fabric's basic building blocks, the
:doc:`operations <api/operations>`. Not only are these the most commonly
utilized parts of Fabric's API in user fabfiles, but they're also what form the
foundation for the rapidly growing :ref:`contrib <contrib-api>` section of the
codebase.

Follow any link containing the name of an operation to view its API
documentation with complete details on its use. There are a number of
additional options for most functions, which we won't be going into here, so
we highly recommend reading the API documentation.

`~fabric.operations.run` and `~fabric.operations.sudo`
------------------------------------------------------

You've already seen how `~fabric.operations.run` executes a given command in a
remote shell; it has a close cousin, `~fabric.operations.sudo`, which is
identical save for the fact that it automatically wraps your command inside a
``sudo`` call, and is capable of detecting ``sudo``'s password prompt.

.. note::

    Hyperlinked versions of the word "sudo" (e.g. `~fabric.operations.sudo`)
    refer to the Python function; non-hyperlinked, monospaced versions
    (``sudo``) refer to the command-line program which the function uses.

A simple example, defining a useful subroutine for restarting services on a
Linux system::

    from fabric.api import sudo

    def restart(service):
        sudo('/etc/init.d/%s restart' % service)

Assuming you haven't recently entered your password on the remote system, a
password prompt will appear, which Fabric will detect and pass through to you::

    $ fab -H example.com restart:service=apache2
    [example.com] sudo: /etc/init.d/apache2 restart
    Password for username@example.com: 
    [example.com] out: Restarting web server apache2
    [example.com] out: ...done.

    Done.
    Disconnecting from example.com... done.

The above usage example highlights a couple new features:

* ``fab``'s ``-H`` option, allowing you to define the host or hosts to
  connect to. See :doc:`fab` for details on other options the ``fab`` tool
  accepts, and read :ref:`hosts` below to learn about the various different
  ways in which you can tell Fabric what servers to talk to.
* The ability to specify task arguments on the command line. :doc:`fab` also
  discusses this aspect of command-line use.

.. note::

    Both `~fabric.operations.run` and `~fabric.operations.sudo` wrap your
    command in a call to a shell binary, loading your login files for a
    smoother experience. However, this can occasionally cause problems with
    complex commands, and may be disabled by specifying ``shell=False``.

Finally, for more details on how `~fabric.operations.run`
and `~fabric.operations.sudo` interact with the SSH protocol -- including the
shell loaded on the remote end, key-based authentication and more -- please
see :doc:`foo`.

`~fabric.operations.local`
--------------------------

While much of the Fabric API deals with remote servers, we've included a
convenient wrapper around the Python stdlib's ``subprocess`` library called
`~fabric.operations.local`. `~fabric.operations.local` does not make network
connections, running (as you might expect) locally instead, but is otherwise
similar to `~fabric.operations.run` and `~fabric.operations.sudo`: it takes a
command string, invokes it in a shell, and is capable of printing and/or
capturing the resulting output.

.. note::

    At the present time, `~fabric.operations.local`'s behavior is not a perfect
    copy of that seen in `~fabric.operations.run` and
    `~fabric.operations.sudo` -- for example, it cannot capture **and** print
    at the same time. This is likely to improve by the time Fabric 1.0 is
    released.

Here's a sample taken from Fabric's own internal fabfile, which executes the
test suite and displays the output::

    from fabric.api import local

    def test():
        print(local('nosetests -sv --with-doctest', capture=False))

A truncated version of the output::

    $ fab test
    [localhost] run: nosetests -sv --with-doctest
    Doctest: fabric.operations._shell_escape ... ok
    Aborts if any given roles aren't found ... ok
    Use of @roles and @hosts together results in union of both ... ok
    If @hosts is used it replaces any env.hosts value ... ok
    [...]
    Aliases can be nested ... ok
    Alias expansion ... ok
    warn() should print 'Warning' plus given text ... ok
    indent(strip=True): Sanity check: 1 line string ... ok
    abort() should raise SystemExit ... ok
    ----------------------------------------------------------------------
    Ran 63 tests in 0.606s

    OK


    Done.

`~fabric.operations.put` and `~fabric.operations.get`
-----------------------------------------------------

In addition to executing shell commands, Fabric leverages SFTP to allow
uploading and downloading of files, via the `~fabric.operations.put` and
`~fabric.operations.get` functions respectively. The builtin contrib
function `~fabric.contrib.project.upload_project` combines
`~fabric.operations.local`, `~fabric.operations.run` and
`~fabric.operations.put` to transmit a copy of the current project to the
remote server, and serves as a good example of what we've seen so far. What
follows is a modified version of the real thing::

    from fabric.api import local, put, run

    def upload_project():
        fname = "project.tgz"
        fpath = "/tmp/%s" % fname
        local("tar -czf %s ." % fpath)
        dest = "/var/www/%s" % fname
        put(fpath, dest)
        run("cd /var/www && tar -xzf %s" % fname)
        run("rm -f %s" % dest)

Running it doesn't provide much output, provided things go well (which is
generally the Unix way -- be silent unless something is wrong -- and this is
followed by the commands we call here: ``tar``, ``cd`` and ``rm``)::

    $ fab -H example.com upload_project
    [localhost] run: tar -czf /tmp/project.tgz .
    [ubuntu904] put: /tmp/project.tgz -> /var/www/project.tgz
    [ubuntu904] run: cd /var/www && tar -xzf project.tgz
    [ubuntu904] run: rm -f /var/www/project.tgz

`require` and `~fabric.operations.prompt`
-----------------------------------------

Finally, Fabric's operations contain a couple convenience methods:
`~fabric.operations.require` and `~fabric.operations.prompt`.
`~fabric.operations.require` lets you ensure that a task will abort if some
needed information is not present, which can be handy if you have a small
network of inter-operating tasks (see :ref:`env` below for more.) You can
probably guess what `~fabric.operations.prompt` does -- it's a convenient
wrapper around Python's ``raw_input`` builtin that asks the user to enter a
string, useful for interactive tasks.

For details and examples, please see the relevant API documentation.


.. _environment:

The environment
===============

A simple but integral aspect of Fabric is what is known as the "environment": a
Python dictionary subclass which is used as a combination settings registry and
shared inter-task data namespace. You've already seen it in action during the
:ref:`introduction` when it was used to set the ``host_string`` setting.

Environment as configuration
----------------------------

Most of Fabric's behavior is controllable by modifying env variables in the
same way that ``host_string`` was used in the :ref:`introduction`; other
commonly-modified env vars are:

* ``hosts`` and ``roledefs``: more commonly used than ``host_string``, these
  allow control of the host or hosts which Fabric connects to when it runs. See
  :ref:`hosts` for details.
* ``user`` and ``password``: Fabric uses your local username by default, and
  will prompt you for connection and sudo passwords as necessary -- but you can
  always specify these explicitly if you need to. The :ref:`hosts` section also
  has info on how to specify usernames on a per-host basis.
* ``warn_only``: a Boolean setting determining whether Fabric exits when
  detecting errors on the remote end. See :ref:`execution` for more on this
  behavior.

For a full list of environment variables Fabric makes use of, see :doc:`env`.

It's possible (and useful) to temporarily modify ``env`` vars by means of the
``settings`` context manager, which will override the given key/value pairs in
``env`` within the wrapped block only. For example, if you expect a given
command may fail but wish to continue executing your task regardless, wrap it
with ``settings(warn_only=True):``, as seen in this simplified version of the
contrib `~fabric.contrib.files.exists` function::

    from fabric.api import settings, run

    def exists(path):
        with settings(warn_only=True):
            return run('test -e %s' % path)

See the :doc:`api/context_managers` API documentation for details on
`~fabric.context_managers.settings` and other, similar tools.

Environment as shared state
---------------------------

As mentioned, the ``env`` object is simply a dictionary subclass, so your own
fabfile code may store information in it as well. This is sometimes useful for
keeping state between multiple tasks within a single execution run.

.. note::

    This aspect of ``env`` is largely historical: in the past, fabfiles were
    not pure Python and thus the environment was the only way to communicate
    between tasks. Nowadays, you may call other tasks or subroutines directly,
    and even keep module-level shared state if you wish.

    However, in future versions, Fabric will become threadsafe and
    parallel-friendly, at which point ``env`` may be the only easy/safe way to
    keep global state.

Other considerations
--------------------

Finally, note that ``env`` has been modified so that its values may be
read/written by way of attribute access, again as seen in the
:ref:`introduction`. In other words, ``env.host_string`` and
``env['host_string']`` are functionally identical. We feel that attribute
access can often save a bit of typing and makes the code more readable, so it's
the recommended way to interact with ``env``.

However, the fact that it's a dictionary can be useful in other ways, such as
with Python's dict-based string interpolation, which is especially handy if you
need to insert multiple env vars into a single string. Using "normal" string
interpolation might look like this::

    print("Executing on %s as %s" % (env.host, env.user))

Using dict-style interpolation is more readable and slightly shorter::

        print("Executing on %(host)s as %(user)s" % env)


Execution model
===============

So far, we've seen relatively simple examples, but in real-world use things
aren't always so straightforward. To utilize Fabric successfully, you'll need
to understand the basics about how it decides what to do and in what order.

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
run against a single host at a time, allowing for shell-script-like logic.

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

Failure handling
----------------

As we mentioned earlier during the introduction of the
`~fabric.context_managers.settings` context manager, Fabric defaults to a
"fail-fast" behavior pattern: if anything goes wrong, such as a remote program
returning a nonzero return value, execution will halt immediately.

This is typically the desired behavior, but there are many exceptions to the
rule, so Fabric provides a ``warn_only`` Boolean setting that, if set to True
at the time of failure, causes Fabric to emit a warning message but continue
executing.

Output controls
---------------

Fabric is verbose by default, allowing you to see what's going on at any given
moment: it prints out which tasks it's executing, what commands
`~fabric.operations.run`, `~fabric.operations.sudo` and
`~fabric.operations.local` are running, and the contents of the remote end's
standard output and error.

However, in many situations this verbosity can result in a large amount of
output, and to help you handle it, Fabric provides two context managers:
`~fabric.context_managers.hide` and `~fabric.context_managers.show`. These take
one or more strings naming various output groups to hide or show, respectively.

Building upon an earlier example, the below shows how the contrib
`~fabric.contrib.files.exists` function can hide the normal ``[run] test -e
<path>`` line, and its standard output, so as to not clutter up your terminal
during a simple operation::

    from fabric.api import settings, run, hide

    def exists(path):
        with settings(hide('running', 'stdout'), warn_only=True):
                return run('test -e %s' % path)

.. note::

    While `~fabric.context_managers.hide` is a standalone context manager, we
    use it here inside of `~fabric.context_managers.settings`, which is capable
    of combining other context managers as well as performing its own function.
    This helps prevent your fabfile from having too many indent levels.

See :doc:`output_levels` for details on the various output levels available, as
well as further notes on the use of `~fabric.context_managers.hide` and
`~fabric.context_managers.show`.


Conclusion
==========

This concludes the tutorial and overview. We've only touched on the basics
here; we hope you've been following the provided links to the detailed
documentation on various topics. For the full documentation list, see :ref:`the
index page <prose-docs>`.
