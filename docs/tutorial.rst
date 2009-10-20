=====================
Overview and Tutorial
=====================

Welcome to Fabric! This document will give you a quick, whirlwind tour of what
Fabric is and how to use it. Detailed usage documentation exists
:ref:`elsewhere <usage-docs>` and is linked to throughout -- please make sure
to follow the links for extra information.


.. _introduction:

Introduction: What is Fabric?
=============================

Fabric is a Python package primarily designed to do two things:

* Run Python functions from the command line, with the ``fab`` tool;
* Execute shell commands locally or on remote servers, with the Fabric library.

We'll tackle these in order, and then see how to use them together, which is
the primary use case.

Python on the command line: the ``fab`` tool
--------------------------------------------

Fabric's main interface is a command-line script called ``fab``, which is
designed to load a Python module (or "fabfile") and execute one or more of
the functions defined within (also known as "tasks" or "commands".)

A "Hello World" example of this would be creating a ``fabfile.py`` somewhere
with the following contents::

    def hello():
        print("Hello, world!")

The ``hello`` task can then be executed with ``fab`` like so, provided you're
in the same directory as the ``fabfile.py`` (or any directory higher up)::

    $ fab hello
    Hello, world!

    Done.

That's all there is to it: define one or more tasks, then ask ``fab`` to
execute them. For details on ``fab``'s behavior and its options/arguments,
please see :doc:`usage/fab`.

.. _library-usage:

Local and remote shell commands: the Fabric library
---------------------------------------------------

Fabric provides a number of core API functions (sometimes referred to as
"operations") for executing shell commands and related functionality.

Use of this API is relatively simple: set an :doc:`environment variable
<usage/env>` telling Fabric what server to talk to, and call the desired
function or functions.

Here's an interactive Python session making use of the `~fabric.operations.run`
function (which executes the given command in a remote Unix shell and returns
the output) where we list the document-root folders on a hypothetical Web
server::

    $ python
    >>> from fabric.api import run, env
    >>> from fabric.state import connections
    >>> env.host_string = 'example.com'
    >>> result = run("ls /var/www")
    [example.com] run: ls
    [example.com] out: www.example.com
    [example.com] out: code.example.com
    [example.com] out: webmail.example.com
    >>> connections['example.com'].close()
    >>> ^D
    $ 

As you can see, `~fabric.operations.run` prints out what it's doing, as well as
the standard output from the remote end, in addition to returning the final
result. More info about how Fabric keeps you updated can be found in
:doc:`usage/output_controls`.

.. note::

    The use of the ``connections`` object to close the connection is necessary
    in order to cleanly exit the Python interpreter. This is less than ideal,
    and Fabric's usability as a library is expected to improve in version 1.0.
    In normal use, you won't have to worry about this -- see the next section.

Putting them together
---------------------

These two aspects of Fabric can be used separately, but the main use case is to
combine them by using ``fab`` to execute tasks utilizing the API functions.
Most of Fabric's auxiliary functions and tools revolve around using it in this
manner.

Here's an example which simply takes the previous interactive example and drops
it into a fabfile::

    from fabric.api import run, env

    def list_docroots():
        env.host_string = 'example.com'
        result = run("ls /var/www")

.. note::

    When using functions like `~fabric.operations.run` in ``fab``-driven
    fabfiles, you don't need to bother with the ``connections`` object -- it's
    handled for you by ``fab``'s main execution loop. See
    :doc:`usage/execution` for more on how the ``fab`` tool handles
    connections.

The result is much the same as before::

    $ fab list_docroots

    [example.com] run: ls
    [example.com] out: www.example.com
    [example.com] out: code.example.com
    [example.com] out: webmail.example.com

    Done.
    Disconnecting from example.com... done.
