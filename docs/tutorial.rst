=====================
Overview and Tutorial
=====================

This document provides a high level overview of how to use Fabric, starting
with basic concepts and moving through progressively more complex (and
realistic!) example code. It tries to leave in-depth explanations to the rest
of the documentation, which is linked to in a number of places.

You will need Fabric :doc:`installed <installation>` in order to follow along.


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
and executing any functions defined within. Functions designed for use with
Fabric are referred to as "tasks" or "commands", and are pure Python code.

Let's start with a typical Hello World example. Create a ``fabfile.py`` in your
current directory and enter the following (and only the following: no imports
are necessary)::

    def hello():
        print("Hello, world!")

Once you've saved this fabfile, you can execute the ``hello`` task with the
``fab`` command-line tool::

    $ fab hello
    Hello, world!

    Done.

That's all there is to it. Since a fabfile is simply a Python module, the sky's
the limit. However, most of the time you'll be interested in using the other
side of Fabric: its SSH functionality.

For details on ``fab``'s behavior and its options/arguments, please see
:ref:`fab`.

Shell commands executed via SSH
-------------------------------

Fabric provides a number of API functions (sometimes referred to as
"operations") including two core functions which connect to remote servers
and execute their arguments as shell commands. These are roughly equivalent to
using the command-line SSH tool with extra arguments, e.g.::

  $ ssh myserver sudo /etc/init.d/apache2 reload

Use of this SSH API is relatively simple: just set an "environment" variable
telling Fabric what server to talk to, and call your desired function. The most
basic such function is `run`, which calls a shell with the given command and
returns the command's output (printing out what it's doing all the while.)
Here's an interactive Python session making use of `run`::

    $ python
    Python 2.5.1 (r251:54863, Feb  9 2009, 18:49:36) 
    [GCC 4.0.1 (Apple Inc. build 5465)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
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
    ideal, and Fabric's use as a library is expected to improve in version 1.0.

Putting them together
---------------------

While these two primary features of Fabric can be used separately, the main use
case is to combine them, defining and running (via ``fab``) task functions
which in turn import and use Fabric's API calls such as `run`. Most of Fabric's
auxiliary functions and tools revolve around this mode of use.

Here's an example which simply takes the previous interactive example and drops
it into a fabfile::

    from fabric.api import run, env

    def list_home():
        env.host_string = 'localhost'
        result = run('ls')

.. note::

    When using functions like `run` in ``fab``-driven fabfiles, you don't need
    to bother with the ``connections`` object -- it's handled for you by
    ``fab``'s main execution loop. See :ref:`execution` for more on how the
    ``fab`` tool handles host connections.

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
operations. Not only are these the most commonly utilized parts of Fabric's API
in user fabfiles, but they're also what form the foundation for the rapidly
growing ``contrib`` section of the codebase.

Follow any link containing the name of an operation to view its API
documentation with complete details on its use.

`run` and `sudo`
----------------

You've already seen how `run` executes a given command in a remote shell; it
has a close cousin, `sudo`, which is identical save for the fact that it
automatically wraps your command inside a ``sudo`` call, and is capable of
detecting ``sudo``'s password prompt.

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

* The ``fab -H`` command-line flag, allowing you to define the host or hosts to
  connect to. See :doc:`fab` for details on other options the ``fab`` tool
  accepts; and see :ref:`hosts` for more on setting host lists.
* The ability to specify task arguments on the command line. :doc:`fab` also
  discusses this aspect of command-line use.

Finally, for more details on how `run` and `sudo` interact with the SSH
protocol -- including the shell loaded on the remote end, key-based
authentication and more -- please see :doc:`foo`.

`local`
-------

While the rest of the Fabric API deals with remote servers, we've included a
convenient wrapper around the Python stdlib's ``subprocess`` library called
`local`. `local` does not make network connections, but is otherwise similar to
`run` and `sudo` in that it takes a command string, invokes it in a shell, and
is capable of printing and/or capturing the resulting output.

.. note::

    At the present time, `local`'s API is not a perfect copy of that seen in
    `run` and `sudo` -- for example, it cannot capture **and** print at the
    same time. This is likely to improve by the time Fabric 1.0 is released.

Here's a sample taken from Fabric's own internal fabfile, which executes the
test suite and displays the output::

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

`put` and `get`
---------------

In addition to executing shell commands, Fabric leverages SFTP to allow
uploading and downloading of files, via the `put` and `get` functions
respectively. The builtin ``contrib`` function `upload_project` combines
`local`, `run` and `put` to transmit a copy of the current project to the
remote server, and serves as a good example of what we've seen so far. What
follows is a slightly simplified version of the real thing::

    def upload_project():
        fname = "project.tgz"
        fpath = "/tmp/%s" % fname
        local("tar -czf %s ." % fpath)
        dest = "/var/www/%s" % fname
        put(fpath, dest)
        run("cd /var/www && tar -xzf %s" % fname)
        run("rm -f %s" % dest)

Running it doesn't provide much output, provided things go well (which is
generally the Unix way -- be silent unless something is wrong)::

    $ fab -H example.com upload_project
    [localhost] run: tar -czf /tmp/project.tgz .
    [ubuntu904] put: /tmp/project.tgz -> /var/www/project.tgz
    [ubuntu904] run: cd /var/www && tar -xzf project.tgz
    [ubuntu904] run: rm -f /var/www/project.tgz

`require` and `prompt`
----------------------

Finally, Fabric's operations contain a couple convenience methods: `require`
and `prompt`. `require` lets you ensure that a task will abort if some needed
information is not present, which can be handy if you have a small network of
inter-operating tasks (see :ref:`env` below for more.) You can probably guess
what `prompt` does -- it's a convenient wrapper around Python's `raw_input`
builtin that asks the user to enter a string, useful for interactive fabfile
tasks.



env

* intro to env

Execution model

* execution model (ties fab tool, fabfiles together?)

  * build task list

    * so keep other callables out of the fabfile!

  * build host list for each task
  * for each task, then for each host for that task, execute
  * fail-fast unless warn_only
  * plan to add more in future
  * not threadsafe/parallelizable right now

* output controls

   * quick info
   * link to detailed page

     * or is what we have in usage.rst really all there is to it?
     * it won't be once we beef it up more...

etc

* you saw the links scattered throughout; see the docs index (link to index
  page, doc section) for the full list
