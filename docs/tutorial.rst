=====================
Overview and Tutorial
=====================

Welcome to Fabric!

This document is a whirlwind tour of Fabric's features and a quick guide to its
use. Additional documentation (which is linked to throughout) can be found in
the :ref:`usage documentation <usage-docs>` -- please make sure to check it out.


What is Fabric?
===============

As the ``README`` says:

    .. include:: ../README
        :end-before: It provides

More specifically, Fabric is:

* A tool that lets you execute **arbitrary Python functions** via the **command
  line**.
* A library of functions (built on top of a lower-level library) to make
  executing shell commands over SSH **easy** and **Pythonic**;

Naturally, most users combine these two things, using Fabric to write and
execute Python functions, or **tasks**, to automate interactions with remote
servers. Let's take a look.


Hello, ``fab``
==============

This wouldn't be a proper tutorial without "the usual"::

    def hello():
        print("Hello world!")

Placed in a file called ``fabfile.py``, that function can be executed with the
``fab`` tool (installed as part of Fabric) and does just what you'd expect::

    $ fab hello
    Hello world!

    Done.

That's all there is to it. This functionality allows Fabric to be used as a
(very) basic build tool even without importing any of its API.

.. seealso:: :doc:`usage/execution`, :doc:`usage/fabfiles`


Local commands
==============

Without importing anything, ``fab`` just saves a couple lines of ``if __name__
== "__main__"`` boilerplate. It's mostly designed for use with Fabric's API,
which contains functions (or **operations**) for executing shell commands,
moving files around, and so forth.

Let's build a hypothetical Web application fabfile. Fabfiles work best at the
root of a project (because they can be picked up by ``fab`` while anywhere
inside the project)::

    .
    |-- __init__.py
    |-- app.wsgi
    |-- fabfile.py <-- our fabfile!
    |-- manage.py
    `-- my_app
        |-- __init__.py
        |-- models.py
        |-- templates
        |   `-- index.html
        |-- tests.py
        |-- urls.py
        `-- views.py

.. note::

    We're using a Django application here, but only as an example -- Fabric is
    not tied to any external codebase, save for its SSH library.

For starters, perhaps we want to run our tests and then check changes into our
SCM so we're ready for a deploy::

    from fabric.api import local

    def prepare_deploy():
        local('./manage.py test my_app', capture=False)
        local('git commit -a', capture=False)

The output of which might look a bit like this::

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

The code itself is straightforward: import a Fabric API function,
`~fabric.operations.local`, and use it to run local shell commands. The rest of
Fabric's API is similar -- it's all just Python.


Prompting
---------

Our ``git commit`` call didn't do anything this time, but if we had modified
files it would've popped open our editor for a commit message. Let's use
`~fabric.operations.prompt` to prompt the user instead::

    from fabric.api import local, prompt

    def prepare_deploy():
        local('./manage.py test my_app', capture=False)
        commit_msg = prompt("Commit message:")
        local('git commit -a -m "%s"' % commit_msg, capture=False)

We won't bore you with a near repetition of the earlier output -- the only
difference will be a text prompt waiting for input from the user.

Fabric has a number of core operations like these, more of which will be
popping up later. For a full list, see the below link to the API documentation.

.. seealso:: :doc:`api/core/operations`


Organize it your way
====================

Because Fabric is "just Python" you're free to organize your fabfile any way
you want. For example, it's often useful to start splitting things up into
subtasks::

    from fabric.api import local, prompt

    def test():
        local('./manage.py test my_app', capture=False)

    def commit():
        commit_msg = prompt("Commit message:")
        local('git commit -a -m "%s"' % commit_msg, capture=False)

    def prepare_deploy():
        test()
        commit()

The ``prepare_deploy`` task can be called just as before, but now you can make
a more granular call to one of the sub-tasks, if desired.

.. note::

    Fabric will let you execute any public callable in your fabfile, so you can
    even import tasks defined in other Python modules or packages.

.. seealso:: :doc:`usage/fabfiles`


Failure
=======

Our base case works fine now, but what happens if our tests fail?  Chances are
we want to put on the brakes and fix them before committing or deploying.

Fabric checks the return value of programs called via operations and will abort
if they didn't exit cleanly. Let's see what happens if one of our tests
encounters an error::

    $ fab prepare_deploy
    [localhost] run: ./manage.py test my_app
    Creating test database...
    Creating tables
    Creating indexes
    .............E............................
    ======================================================================
    ERROR: testSomething (my_project.my_app.tests.MainTests)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    [...]

    ----------------------------------------------------------------------
    Ran 42 tests in 9.138s

    FAILED (errors=1)
    Destroying test database...

    Fatal error: local() encountered an error (return code 2) while executing './manage.py test my_app'

    Aborting.

Great! We didn't have to do anything ourselves: Fabric detected the failure and
aborted.

Coping with failure
-------------------

But what if we wanted to be flexible and give the user a choice? A setting
called :ref:`warn_only` lets you turn aborts into warnings, allowing flexible
error handling to occur.

Let's flip this setting on for our ``test`` function, and then inspect the
result of our `~fabric.operations.local` call ourselves::

    from __future__ import with_statement
    from fabric.api import local, prompt, settings, abort
    from fabric.contrib.console import confirm

    def test():
        with settings(warn_only=True):
            result = local('./manage.py test my_app', capture=False)
        if result.failed and not confirm("Tests failed. Continue anyway?"):
            abort("Aborting at user request.")

    [...]

In adding this new feature we've introduced a number of new things:

* The ``__future__`` import required to use ``with:`` in Python 2.5;
* Fabric's `contrib.console <fabric.contrib.console>` submodule, containing the
  `~fabric.contrib.console.confirm` function, used for simple yes/no prompts;
* The `~fabric.context_managers.settings` context manager, used to apply
  settings to a specific block of code;
* And the `~fabric.utils.abort` function, used to manually abort execution.

However, despite the additional complexity, it's still pretty easy to follow,
and we now have a solid test task in place.

.. seealso:: :doc:`usage/execution`, :doc:`api/core/context_managers`
