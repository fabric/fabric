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
  line**;
* A library of subroutines (built on top of a lower-level library) to make
  executing shell commands over SSH **easy** and **Pythonic**.

Naturally, most users combine these two things, using Fabric to write and
execute Python functions, or **tasks**, to automate interactions with remote
servers. Let's take a look.


Hello, ``fab``
==============

This wouldn't be a proper tutorial without "the usual"::

    def hello():
        print("Hello world!")

Placed in a Python module file named ``fabfile.py``, that function can be
executed with the ``fab`` tool (installed as part of Fabric) and does just what
you'd expect::

    $ fab hello
    Hello world!

    Done.

That's all there is to it. This functionality allows Fabric to be used as a
(very) basic build tool even without importing any of its API.

.. note::

    The ``fab`` tool simply imports your fabfile and executes the function or
    functions you instruct it to. There's nothing magic about it -- anything
    you can do in a normal Python script can be done in a fabfile!

.. seealso:: :ref:`execution-strategy`, :ref:`tasks-and-imports`, :doc:`usage/fab`


Local commands
==============

As used above, ``fab`` only really saves a couple lines of
``if __name__ == "__main__"`` boilerplate. It's mostly designed for use with
Fabric's API, which contains functions (or **operations**) for executing shell
commands, transferring files, and so forth.

Let's build a hypothetical Web application fabfile. Fabfiles usually work best
at the root of a project::

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

For starters, perhaps we want to run our tests and then pack up a copy of our
app so we're ready for a deploy::

    from fabric.api import local

    def prepare_deploy():
        local('./manage.py test my_app', capture=False)
        local('tar czf /tmp/my_project.tgz .', capture=False)

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

    [localhost] run: tar czf /tmp/my_project.tgz .

    Done.

The code itself is straightforward: import a Fabric API function,
`~fabric.operations.local`, and use it to run local shell commands. The rest of
Fabric's API is similar -- it's all just Python.

.. seealso:: :doc:`api/core/operations`, :ref:`fabfile-discovery`


Organize it your way
====================

Because Fabric is "just Python" you're free to organize your fabfile any way
you want. For example, it's often useful to start splitting things up into
subtasks::

    from fabric.api import local

    def test():
        local('./manage.py test my_app', capture=False)

    def pack():
        local('tar czf /tmp/my_project.tgz .', capture=False)

    def prepare_deploy():
        test()
        pack()

The ``prepare_deploy`` task can be called just as before, but now you can make
a more granular call to one of the sub-tasks, if desired.


Failure
=======

Our base case works fine now, but what happens if our tests fail?  Chances are
we want to put on the brakes and fix them before deploying.

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
aborted, never running the ``pack`` task.

.. seealso:: :ref:`Failure handling (usage documentation) <failures>`

Failure handling
----------------

But what if we wanted to be flexible and give the user a choice? A setting
(or **environment variable**, usually shortened to **env var**) called
:ref:`warn_only` lets you turn aborts into warnings, allowing flexible error
handling to occur.

Let's flip this setting on for our ``test`` function, and then inspect the
result of the `~fabric.operations.local` call ourselves::

    from __future__ import with_statement
    from fabric.api import local, settings, abort
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
* Command-running operations like `~fabric.operations.local` return objects
  containing info about their result (such as ``.failed``, or also
  ``.return_code``);
* And the `~fabric.utils.abort` function, used to manually abort execution.

However, despite the additional complexity, it's still pretty easy to follow,
and is now much more flexible.

.. seealso:: :doc:`api/core/context_managers`, :ref:`env-vars`


Making connections
==================

Let's start wrapping up our fabfile by putting in the keystone: a ``deploy``
task::

    def deploy():
        put('/tmp/my_project.tgz', '/tmp/')
        with cd('/srv/django/my_project/'):
            run('tar xzf /tmp/my_project.tgz')
            run('touch app.wsgi')

Here again, we introduce a handful of new functions:

* `~fabric.operations.put`, which simply uploads a file to a remote server;
* `~fabric.context_managers.cd`, an easy way of prefixing commands with a
  ``cd /to/some/directory`` call;
* `~fabric.operations.run`, which is similar to `~fabric.operations.local` but
  runs remotely instead of locally.

And because at this point, we're using a nontrivial number of Fabric's API
functions, let's switch our API import to use ``*`` (as mentioned in the
:doc:`fabfile <usage/fabfiles>` documentation)::

    from __future__ import with_statement
    from fabric.api import *
    from fabric.contrib.console import confirm

With these changes in place, let's deploy::

    $ fab deploy
    No hosts found. Please specify (single) host string for connection: my_server
    [my_server] put: /tmp/my_project.tgz -> /tmp/my_project.tgz
    [my_server] run: touch app.wsgi

    Done.

We never specified any connection info in our fabfile, so Fabric prompted us at
runtime. Connection definitions use SSH-like "host strings" (e.g.
``user@host:port``) and will use your local username as a default -- so in this
example, we just had to specify the hostname, ``my_server``.

.. seealso:: :ref:`importing-the-api`

.. _defining-connections:

Defining connections beforehand
-------------------------------

Specifying connection info at runtime gets old real fast, so Fabric provides a
handful of ways to do it in your fabfile or on the command line. We won't cover
all of them here, but we will show you the most common one: setting the global
host list, :ref:`env.hosts <hosts>`.

:doc:`env <usage/env>` is a global dictionary-like object driving many of
Fabric's settings, and can be written to with attributes as well (in fact,
`~fabric.context_managers.settings`, seen above, is simply a wrapper for this.)
Thus, we can modify it at module level near the top of our fabfile like so::

    from __future__ import with_statement
    from fabric.api import *
    from fabric.contrib.console import confirm

    env.hosts = ['my_server']

    def test():
    [...]

When ``fab`` loads up our fabfile, our modification of ``env`` will execute,
storing our settings change. The end result is exactly as above: our ``deploy``
task will run against the ``my_server`` server.

This is also how you can tell Fabric to run on multiple remote systems at once:
because ``env.hosts`` is a list, ``fab`` iterates over it, calling the given
task once for each connection.

.. seealso:: :doc:`usage/env`, :ref:`host-lists`


Conclusion
==========

Our completed fabfile is still pretty short, as such things go. Here it is in
its entirety::

    from __future__ import with_statement
    from fabric.api import *
    from fabric.contrib.console import confirm

    env.hosts = ['my_server']

    def test():
        with settings(warn_only=True):
            result = local('./manage.py test my_app', capture=False)
        if result.failed and not confirm("Tests failed. Continue anyway?"):
            abort("Aborting at user request.")

    def pack():
        local('tar czf /tmp/my_project.tgz .', capture=False)

    def prepare_deploy():
        test()
        pack()

    def deploy():
        put('/tmp/my_project.tgz', '/tmp/')
        with cd('/srv/django/my_project/'):
            run('tar xzf /tmp/my_project.tgz')
            run('touch app.wsgi')

This fabfile makes use of a large portion of Fabric's feature set:

* defining fabfile tasks and running them with :doc:`fab <usage/fab>`;
* calling local shell commands with `~fabric.operations.local`;
* modifying env vars with `~fabric.context_managers.settings`;
* handling command failures, prompting the user, and manually aborting;
* and defining host lists and `~fabric.operations.run`-ning remote commands.

However, there's still a lot more we haven't covered here! Please make sure you
follow the various "see also" links, and check out the documentation table of
contents on :ref:`the main index page <documentation-index>`.

Thanks for reading!
