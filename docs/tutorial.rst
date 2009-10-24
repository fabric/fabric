=====================
Overview and Tutorial
=====================

Welcome to Fabric!

This document is a whirlwind tour of Fabric's features and a quick guide to its
use. Additional documentation (which is linked to throughout) can be found in
the :ref:`usage documentation <usage-docs>` -- we'll be light on details here,
so please check out the links.


What is Fabric?
===============

As the ``README`` says:

    .. include:: ../README
        :end-before: It provides

More specifically, Fabric is:

* A library of functions (built on top of a lower-level library) to make
  executing shell commands over SSH **easy** and **Pythonic**;
* A tool that lets you execute **arbitrary Python functions** via the **command
  line**.

Naturally, most users combine these two things, using Fabric to write and
execute Python functions, or **tasks**, to automate interactions with remote
servers. Let's take a look.


Starting out
============

This wouldn't be a proper tutorial without "the usual"::

    def hello():
        print("Hello world!")

Placed in a file called ``fabfile.py`` (without any other code whatsoever!)
that function can be executed with the ``fab`` tool (installed as part of
Fabric) and does just what you'd expect::

    $ fab hello
    Hello world!

    Done.

That's all there is to it. This functionality allows Fabric to be used as a
(very) basic build tool even without importing any of its API.

.. seealso:: :doc:`usage/execution`, :doc:`usage/fabfiles`


Using operations
================

While convenient, the ``fab`` tool isn't very interesting, only saving you the
usual ``if __name__ == "__main__"`` stuff. It's designed to be paired with
Fabric's API full of functions for executing commands, moving files around, and
so forth. Functions in this API are sometimes called **operations**.

Let's start building a hypothetical Web application fabfile. Fabfiles work best when at the root of a project source tree (because they can be picked up by ``fab`` while anywhere inside the tree)::

    .
    |-- __init__.py
    |-- app.wsgi
    |-- fabfile.py <-- our fabfile!
    |-- manage.py
    |-- media
    |   |-- global.js
    |   |-- img
    |   |   `-- favicon.ico
    |   `-- screen.css
    `-- my_app
        |-- __init__.py
        |-- models.py
        |-- templates
        |   `-- index.html
        |-- tests.py
        |-- urls.py
        `-- views.py

.. note::

    The above, for those familiar with it, is a Django application. However,
    Fabric isn't tied to any external codebase unless you explicitly import
    one -- this is solely an example!

Starting out, perhaps we want to just have a task that runs our tests and then
checks any changed files into our SCM so we're ready for a SCM-based deploy::

    from fabric.api import local

    def prepare_deploy():
        local('./manage.py test my_app', capture=False)
        local('git commit -a', capture=False)

The output of which might look like this::

    $ fab prepare_deploy
    [localhost] run: ./manage.py test my_app
    Creating test database...
    Creating tables
    Creating indexes
    ..........................................
    ----------------------------------------------------------------------
    Ran 42 tests in 9.138s

    OK
    Destroying test database...

    [localhost] run: git commit -a
    # On branch master
    nothing to commit (working directory clean)

    Done.

Hopefully the code itself is pretty obvious: import a Fabric API function, `~fabric.operations.local`, and use it to run some local shell commands. Using the rest of Fabric's API is similarly straightforward -- it's all just Python.

If you're familiar with Git, you'll notice that while our ``git commit`` call
didn't do anything this time, if we had modified files it would've popped open
our editor for a commit message. Let's use another operation,
`~fabric.operations.prompt`, to prompt the user for the commit message
instead::

    from fabric.api import local, prompt

    def prepare_deploy():
        local('./manage.py test my_app', capture=False)
        commit_msg = prompt("Commit message:")
        local('git commit -a -m "%s"' % commit_msg, capture=False)

We won't bore you with a near repetition of the earlier output -- the only difference will be a simple prompt popping up waiting for input from the user.

Fabric has a number of core operations like these, more of which will be
popping up later. For a full list, see the below link to the API documentation.

.. seealso:: :doc:`api/core/operations`


Organize it your way
====================

As mentioned, Fabric is just Python, so you're free to organize your fabfile any way you want -- do what works for you. In this case, we might find it useful to start splitting things up into subtasks::

    from fabric.api import local, prompt

    def test():
        local('./manage.py test my_app', capture=False)

    def commit():
        commit_msg = prompt("Commit message:")
        local('git commit -a -m "%s"' % commit_msg, capture=False)

    def prepare_deploy():
        test()
        commit()

The ``prepare_deploy`` task can be called just as before, but now you can make a more granular call to one of the sub-tasks, if desired. Fabric will let you execute any public callable in your fabfile, so you can even import from other Python modules or packages.

.. seealso:: :doc:`usage/fabfiles`


Coping with failure
===================

Our fabfile is coming along nicely, but what happens if our tests fail?
