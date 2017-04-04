.. _upgrading:

=========================
Upgrading from Fabric 1.x
=========================

Fabric 2 represents a near-total reimplementation & reorganization of the
software. It's been broken in two, cleaned up, made more explicit, and so
forth. In some cases, upgrading requires only basic search & replace; in
others, more work is needed.

If you read this document carefully, it should guide you in the right direction
until you're fully upgraded. Should anything be missing, please file a ticket
`on Github <https://github.com/fabric/fabric>`_ and we'll update it ASAP.

General / conceptual
====================

- All of Fabric 1's non-SSH-specific functionality (CLI parsing, task
  organization, command execution basics, etc) has been moved to a more general
  library called `Invoke <http://pyinvoke.org>`_. Fabric 2 builds on Invoke
  (and as before, on Paramiko) to present an SSH-specific API.

  .. warning::
    Please check Invoke's documentation before filing feature request tickets!

- The CLI task-oriented workflow remains a primary design goal, but the library
  use case is no longer a second-class citizen; instead, the library
  functionality has been designed first, with the CLI/task features built on
  top of it.
- Invoke's design includes :ref:`explicit user-facing testing functionality
  <testing-user-code>`; if you didn't find a way to write tests for your
  Fabric-using code before, it should be much easier now.

    - We recommend trying to write tests early on; they will help clarify the
      upgrade process for you & also make the process safer!

API organization
================

- There's no longer a need to import everything through ``fabric.api``; all
  useful imports are now available at the top level, e.g. ``from fabric import
  Connection``.
- Speaking of: the primary API is now "instantiate `.Connection` objects and
  call their methods" instead of "manipulate global state and call module-level
  functions."
- Connections replace *host strings*, which are no longer first-order
  primitives but simply convenient, optional shorthand in a few spots (such as
  `.Connection` instantiation.)
- Connection objects store per-connection state such as user, hostname, gateway
  config, etc, and encapsulate low-level objects from Paramiko (such as their
  ``SSHClient`` instance.)

    - There is also a new ``connect_kwargs`` argument available in
      `.Connection` that takes arbitrary kwargs intended for the Paramiko-level
      ``connect()`` call; this means Fabric no longer needs explicit patches to
      support individual Paramiko features.

- Other configuration state (such as default desired behavior, authentication
  parameters, etc) can also be stored in these objects, and will affect how
  they operate. This configuration is also inherited from the CLI machinery
  when the latter is in use.
- The basic "respond to prompts" functionality found as Fabric 1's
  ``env.prompts`` dictionary option, has been significantly fleshed out into a
  framework of :ref:`Watchers <autoresponding>` which operate on a running
  command's input and output streams.

    - In addition, ``sudo`` has been rewritten to use that framework; while
      it's still useful to have implemented in Fabric (actually Invoke) itself,
      it doesn't use any private internals any longer.

- *Roles* (and other lists-of-host-strings such as the result of using ``-H``
  on the CLI) are now (or can be) implemented via `.Group` objects, which are
  lightweight wrappers around multiple Connections.
- v1's desire to tightly control program state (such as using ``abort()`` and
  ``warn()`` to exit and/or warn users) has been scaled back; instead you
  should simply use whatever methods you want in order to exit, log, and so
  forth.

    - For example, instead of ``abort("oh no!")``, you may just want to ``raise
      MyException("welp")`` or even ``sys.exit("Stuff broke!")``.

CLI tasks
=========

- Fabric-specific command-line tasks now take a `.Connection` object as their
  first positional argument.

    - This sacrifices some of the "quick DSL" of v1 in exchange for a
      significantly cleaner, easier to understand/debug, and more
      user-overrideable, API structure.
    - It also lessens the distinction between "a module of functions" and "a
      class of methods"; users can more easily start with the former and
      migrate to the latter when their needs grow/change.

- Old-style task functions (those not decorated with ``@task``) are gone. You
  must now always use ``@task``. (Note that users heavily attached to old-style
  tasks should be able to reimplement them by extending
  `~invoke.collection.Collection`!)

General shell commands
======================

- All shell command execution is now unified; in v1, ``local()`` and
  ``run()``/``sudo()`` had significantly different signatures and behavior, but
  in v2 they all use the same underlying protocol and logic, with only details
  like process creation and pipe consumption differing.
- Thus, where ``local()`` required you to choose between displaying and
  capturing program output, that dichotomy no longer exists; both local and
  remote execution always captures, and either may conditionally show or hide
  stdout or stderr while the program runs.

Remote shell commands
=====================

- There is no more built-in ``use_shell`` or ``shell`` option; the old "need"
  to wrap with an explicit shell invocation is no longer necessary or usually
  desirable.

Networking
==========

- ``env.gateway`` is now the ``gateway`` kwarg to `.Connection`, and -- for
  ``ProxyJump`` style gateways -- should be another `.Connection` object
  instead of a host string.

    - You may specify a runtime, non-SSH-config-driven ``ProxyCommand``-style
      string as the ``gateway`` kwarg instead, which will act just like a
      regular ``ProxyCommand``.
    - SSH-config-driven ``ProxyCommand`` continues to work as it did in v1.
    - ``ProxyJump``-style gateways (using nested/inner `.Connection` objects)
      may be nested indefinitely, as you might expect.

- ``fabric.context_managers.remote_tunnel`` (which forwards a locally
  visible/open port to the remote end so remote processes may connect to it) is
  now `.Connection.forward_local`.
- Accompanying `.Connection.forward_local` is the logical inversion,
  `.Connection.forward_remote` (forwards a remotely visible port locally),
  which is new in Fabric 2 and was not implemented in Fabric 1 at time of
  writing (though there are patches for it).

Configuration
=============

- General configuration has been massively improved over the old ``fabricrc``
  files; Fabric 2 builds on Invoke which offers a full-fledged configuration
  hierarchy (in-code config, multiple config file locations, environment
  variables, CLI flags, and more) and multiple file formats.

    - Anytime you used to modify Fabric's config by manipulating
      ``fabric.(api.)env`` (or using ``with settings():``), you will now be
      using Invoke-style config manipulation and/or method keyword arguments.
    - See :ref:`Invoke's configuration documentation <configuration>` for
      details on how the system works, where config sources come from, etc; and
      for non-SSH-specific settings, such as whether to hide command output.
    - See :ref:`Fabric's specific config doc page <fab-configuration>` for the
      modifications & additions Fabric makes in this area, such as SSH-specific
      settings like default port number or whether to forward an SSH agent.

- :ref:`SSH config file loading <ssh-config>` has also improved. Fabric 1
  allowed selecting a single SSH config file; version 2 behaves more like
  OpenSSH and will seek out both system and user level config files, as well as
  allowing a runtime config file. (And advanced users may simply supply their
  own Paramiko SSH config object they obtained however.)
- Speaking of SSH config loading, it is **now enabled by default**, and may be
  easily :ref:`disabled <disabling-ssh-config>` by advanced users seeking
  purity of state.
- On top of the various SSH config directives implemented in v1, v2 honors
  ``ConnectTimeout`` and ``ProxyJump``; generally, the intention is now that
  SSH config support is to be included in any new feature added, when
  appropriate.


Example upgrade process
=======================

Sample original fabfile
-----------------------

Here's a (slightly modified to concur with 'modern' Fabric 1 best practices)
copy of Fabric 1's final tutorial snippet, which we will use as our test case
for upgrading::

    from fabric.api import abort, env, local, run, settings, task
    from fabric.contrib.console import confirm

    env.hosts = ['my_server']

    @task
    def test():
        with settings(warn_only=True):
            result = local('./manage.py test my_app', capture=True)
        if result.failed and not confirm("Tests failed. Continue anyway?"):
            abort("Aborting at user request.")

    @task
    def commit():
        local("git add -p && git commit")

    @task
    def push():
        local("git push")

    @task
    def prepare_deploy():
        test()
        commit()
        push()

    @task
    def deploy():
        code_dir = '/srv/django/myproject'
        with settings(warn_only=True):
            if run("test -d {}".format(code_dir)).failed:
                cmd = "git clone user@vcshost:/path/to/repo/.git {}"
                run(cmd.format(code_dir))
        with cd(code_dir):
            run("git pull")
            run("touch app.wsgi")

We'll port this directly, meaning the result will still be ``fabfile.py``,
though we'd like to note that writing your code in a more library-oriented
fashion - even just as functions not wrapped in ``@task`` - can make testing
and reusing code easier.

Imports
-------

In this case, we don't need to import nearly as many functions, due to the
emphasis on object methods instead of global functions. We only need the
following:

- `sys`, for `sys.exit` (replacing ``abort()``);
- `@task <.task>`, as before, but coming from Invoke as it's not SSH-specific;
- ``confirm``, which now comes from the Invocations library (also not
  SSH-specific, and Invocations is one of the descendants of
  ``fabric.contrib``, which no longer exists);

::

    import sys

    from invoke import task
    from invocations.console import confirm

Host list
---------

The idea of a global host lists is gone; there is currently no direct
replacement. Instead, we expect users to set up their own execution context,
creating explicit `.Connection` and/or `.Group` objects as needed, even if
that's simply by mocking v1's built-in "roles" map.

This is an area under active development, so feedback is welcomed.

For now, given the source snippet hardcoded a hostname of ``my_server``, we'll
assume this fabfile will be invoked as e.g. ``fab -H my_server taskname``, and
there will be no hardcoding within the fabfile itself.

.. TODO:
    - pre-task example
    - true baked-in default example (requires some sort of config hook)

Test task
---------

The first task in the fabfile uses a good spread of the API. We'll outline the
changes here (note that these are all listed above as well):

- Declaring a function as a task is nearly the same as before, but with an
  explicit initial context argument, whose value will be a `.Connection` object
  at runtime.
- The use of ``with settings(warn_only=True)`` can be replaced by a simple
  kwarg to the ``local()`` call.
- That ``local()`` call is now a method call on the `.Collection`,
  `.Collection.local`.
- ``capture`` is no longer a useful method; we can now capture and display at
  the same time, locally or remotely. If you don't actually *want* a local
  subprocess to mirror its stdout/err while it runs, you can simply say
  ``hide=True``.
- Result objects are pretty similar in v1 and v2; v2's no longer pretend to
  "be" strings, but instead act more like booleans, acting truthy if the
  command exited cleanly, and falsey otherwise. In terms of attributes
  exhibited, most of the same info is available, with v2 typically exposing
  more than v1.
- ``abort()`` is gone; you should use exceptions or builtins like ``sys.exit``
  instead.

.. TODO: check up on Fabric 2 compatible patchwork for confirm()

The result::

    @task
    def test(c):
        result = c.local('./manage.py test my_app', warn=True)
        if not result and not confirm("Tests failed. Continue anyway?"):
            sys.exit("Aborting at user request.")

Other simple tasks
------------------

The next two tasks are simple one-liners, and you've already seen what replaced
the global ``local()`` function::

    @task
    def commit(c):
        c.local("git add -p && git commit")

    @task
    def push(c):
        c.local("git push")


Calling tasks from other tasks
------------------------------

This is another area that is in flux at the Invoke level, but for now, we can
simply call the other tasks as functions, just as was done in v1. The main
difference is that we want to pass along our context object::

    @task
    def prepare_deploy(c):
        test(c)
        commit(c)
        push(c)


Actual remote steps
-------------------

Note that up to this point, nothing truly Fabric-related has been in play -
`.Connection.local` is just a rebinding of `.Context.run`, Invoke's local
subprocess execution method. Now we get to the actual deploy step, which simply
invokes `.Connection.run` instead, executing remotely (on whichever host the
`.Connection` has been bound to).

``with cd()`` is not yet implemented for the remote side of things, but we
expect it will be soon. For now we fall back to command chaining with ``&&``.

::

    @task
    def deploy(c):
        code_dir = '/srv/django/myproject'
        if not c.run("test -d {}".format(code_dir), warn=True):
            cmd = "git clone user@vcshost:/path/to/repo/.git {}"
            c.run(cmd.format(code_dir))
        run("cd {} && git pull".format(code_dir))
        run("cd {} && touch app.wsgi".format(code_dir))


The whole thing
---------------

Now we have the entire, upgraded fabfile that will work with Fabric 2::

    import sys

    from invoke import task
    from invocations.console import confirm

    @task
    def test(c):
        result = c.local('./manage.py test my_app', warn=True)
        if not result and not confirm("Tests failed. Continue anyway?"):
            sys.exit("Aborting at user request.")

    @task
    def commit(c):
        c.local("git add -p && git commit")

    @task
    def push(c):
        c.local("git push")

    @task
    def prepare_deploy(c):
        test(c)
        commit(c)
        push(c)

    @task
    def deploy(c):
        code_dir = '/srv/django/myproject'
        if not c.run("test -d {}".format(code_dir), warn=True):
            cmd = "git clone user@vcshost:/path/to/repo/.git {}"
            c.run(cmd.format(code_dir))
        run("cd {} && git pull".format(code_dir))
        run("cd {} && touch app.wsgi".format(code_dir))
