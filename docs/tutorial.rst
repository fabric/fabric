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
"operations") including a few, core functions which connect to remote servers
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

A close cousin to `run` is `sudo`, which is identical save for the fact that it
automatically wraps your command inside a ``sudo`` call, and is capable of
detecting ``sudo``'s password prompt. See :ref:`foo` for more on ``sudo`` and
the other SSH-related functions Fabric provides.

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


Nuts and bolts go here
======================

what it does

* Brief overview of the operations / "fabric core api"

  * Explain how we use SSH and what exactly run/sudo do shellwise

    * including explanation of the bin/bash wrapper and how to turn it off
      with shell=False
    * link to detailed docs, e.g. unknown hosts and keys and etc

  * put/get operate one file at a time (paramiko limitation)

    * maybe a "paramiko limitations" page-o-shame? eh

  * local uses subprocess

    * it's not quite the same api/behavior as run/sudo; we hope to change
      this

  * everything else builds on these guys -- your stuff, and our stuff
    (contrib!)

    * link to contrib api docs?

the basic ingredients

* intro to fab tool

  * tries to be good unix citizen
  * overview of most common options, link to an actual doc page

    * do we have one? make one if not

* intro to fabfiles

  * really just restating the intro material?

* intro to env

how it runs

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
