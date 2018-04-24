.. _upgrading:

=========================
Upgrading from Fabric 1.x
=========================

Fabric 2 represents a near-total reimplementation & reorganization of the
software. It's been :ref:`broken in two <invoke-split-from-fabric>`, cleaned
up, made more explicit, and so forth. In some cases, upgrading requires only
basic search & replace; in others, more work is needed.

If you read this document carefully, it should guide you in the right direction
until you're fully upgraded. Should anything be missing, please file a ticket
`on Github <https://github.com/fabric/fabric>`_ and we'll update it ASAP.


'Sidegrading' to Invoke
=======================

We linked to a note about this above, but to be explicit: Fabric 2 is really
two separate libraries, and anything not strictly SSH or network related has
been :ref:`split out into the Invoke project <invoke-split-from-fabric>`.

This means that if you're in the group of users leveraging Fabric solely for
its task execution or ``local()``, and never used ``run()``, ``put()`` or
similar - **you don't need to use Fabric itself anymore** and can simply
**'sidegrade' to Invoke instead**.

You'll still want to read over this document to get a sense of how things have
changed, but be aware that you can get away with ``pip install invoke`` and
won't need Fabric, Paramiko, cryptography dependencies, or anything else.


Why upgrade?
============

We'd like to call out, in no particular order, some specific improvements in
Fabric 2 that might make upgrading worth your time.

.. note::
    These are all listed in the next section as well, so if you're already
    sold, just skip there. TK: double check that this is still true!

- Python 3 compatibility (specifically, we now support 2.7 and 3.4+);
- Thread-safe - no more requirement on multiprocessing for concurrency;
- API reorganized around `.Connection` objects instead of global module state;
- Command-line parser overhauled to allow for regular GNU/POSIX style flags and
  options on a per-task basis (no more ``fab mytask:weird=custom,arg=format``);
- Task organization is more explicit and flexible / has less 'magic';
- Tasks can declare other tasks to always be run before or after themselves;
- Configuration massively expanded to allow for multiple config files &
  formats, env vars, per-user/project/module configs, and much more;
- SSH config file loading enabled by default & has been fleshed out re:
  system/user/runtime file selection;
- Shell command execution API consistent across local and remote method calls -
  no more differentiation between ``local()`` and ``run()`` (besides where the
  command runs, of course!);
- Shell commands significantly more flexible re: interactive behavior,
  simultaneous capture & display (now applies to local subprocesses, not just
  remote), encoding control, and auto-responding;
- Use of Paramiko's APIs for the SSH layer much more transparent - e.g.
  `.Connection` allows control over the kwargs given to `SSHClient.connect
  <paramiko.client.SSHClient.connect>`;
- Gateway/jump-host functionality offers a ``ProxyJump`` style 'native' (no
  proxy-command subprocesses) option, which can be nested infinitely;


Upgrading piecemeal
===================

To help with gradual upgrades, Fabric 2 may be installed under the name
``fabric2`` (in addition to being made available "normally" as version 2.0+ of
``fabric``) and can live alongside installations of version 1.x.

Thus, if you have a large codebase and don't want to make the jump to 2.x in
one leap, it's possible to have both Fabric 1 (``fabric``, as you presumably
had it installed previously) and Fabric 2 (as ``fabric2``) resident in your
Python environment simultaneously.

.. note::
    We strongly recommend that you eventually migrate all code using Fabric 1,
    to version 2 or above, so that you can move back to installing and
    importing under the ``fabric`` name. ``fabric2`` as a distinct package and
    module is intended to be a stopgap, and there will not be any ``fabric3``
    or above (not least because some of those names are already taken!)

For details on how to obtain the ``fabric2`` version of the package, see
:ref:`installing-as-fabric2`.


.. _upgrade-specifics:

Upgrade specifics
=================

This is (intended to be) an exhaustive list of *all* Fabric 1.x functionality,
as well as new-to-Invoke-or-Fabric-2 functionality not present in 1.x; it
specifies whether upgrading is necessary, how to upgrade if so, and tracks
features which haven't been implemented in version 2 yet.

Most sections are broken down in table form, as follows:

.. list-table::

    * - Fabric 1 feature or behavior
      - Status, see below for breakdown
      - Migration notes, removal rationale, etc

The 'status' field will be one of the following:

- **Ported**: available already in v2, possibly renamed or moved (frequently,
  moved into the `Invoke <http://pyinvoke.org>`_ codebase.)
- **Pending**: would fit in v2, but has not yet been ported, good candidate for
  a patch (but please check for a ticket first!)
- **Removed**: explicitly *not* ported (no longer fits with vision, had too
  poor a maintenance-to-value ratio, etc) and unlikely to be reinstated.
- **Mixed**: some combination of the above, such as a feature set that is
  partly ported and partly pending.

Here's a quick local table of contents for navigation purposes:

.. contents::
    :local:

General / conceptual
--------------------

- Fabric 2 is fully Python 3 compatible; as a cost, Python 2.5 support has been
  dropped - in fact, we've dropped support for anything older than Python 2.7.
- The CLI task-oriented workflow remains a primary design goal, but the library
  use case is no longer a second-class citizen; instead, the library
  functionality has been designed first, with the CLI/task features built on
  top of it.
- Additionally, within the CLI use case, version 1 placed too much emphasis on
  'lazy' interactive prompts for authentication secrets or even connection
  parameters, driven in part by a lack of strong configuration mechanisms. Over
  time it became clear this wasn't worth the tradeoffs of having confusing
  noninteractive behavior and difficult debugging/testing procedures.

  Version 2 takes an arguably cleaner approach (based on functionality added to
  v1 over time) where users are encouraged to leverage the configuration system
  and/or serve the user prompts for runtime secrets at the *start* of the
  process; if the system determines it's missing information partway through,
  it raises exceptions instead of prompting.
- Invoke's design includes :ref:`explicit user-facing testing functionality
  <testing-user-code>`; if you didn't find a way to write tests for your
  Fabric-using code before, it should be much easier now.

    - We recommend trying to write tests early on; they will help clarify the
      upgrade process for you & also make the process safer!

.. _upgrading-api:

API organization
----------------

High level code flow and API member concerns.

.. list-table::
    :widths: 40 10 50

    * - Import everything via ``fabric.api``
      - Removed
      - All useful imports are now available at the top level, e.g. ``from
        fabric import Connection``.
    * - Configure connection parameters globally (via ``env.host_string``) and
        call global methods which reference them (``run``/``sudo``/etc)
      - Ported
      - The primary API is now properly OOP: instantiate `.Connection` objects
        and call their methods. These objects encapsulate all connection state
        (user, host, gateway, etc) and have their own SSH client instances.
    * - Emphasis on serialized "host strings" as method of setting user, host,
        port, etc
      - Ported
      - `.Connection` *can* accept a shorthand "host string"-like argument, but
        the primary API is now explicit user, host, port, etc keyword
        arguments.
    * - Use of "roles" as global named lists of host strings
      - Ported
      - This need is now served by `.Group` objects (which wrap some number of
        `.Connection` instances with "do a thing to all members" methods.)
        Users can create & organize these any way they want.

        See the line items for ``--roles`` (:ref:`upgrading-cli`),
        ``env.roles`` (:ref:`upgrading-env`) and ``@roles``
        (:ref:`upgrading-tasks`) for the status of those specifics.

.. _upgrading-tasks:

Task functions & decorators
---------------------------

.. note::
    Nearly all task-related functionality is implemented in Invoke; for more
    details see its :ref:`execution <task-execution>` and :ref:`namespaces
    <task-namespaces>` documentation.

.. list-table::
    :widths: 40 10 50

    * - "Classic" style implicit tasks w/o a ``@task`` decorator
      - Removed
      - These were on the way out even in v1, and arbitrary task/namespace
        creation is more explicitly documented now, via Invoke's
        `~invoke.tasks.Task` and `~invoke.collection.Collection`.
    * - "New" style ``@task``-decorated, module-level task functions
      - Ported
      - Largely the same, though now with superpowers - `@task
        <invoke.tasks.task>` can still be used without any parentheses, but
        where v1 only had a single ``task_class`` argument, Invoke has a number
        of various namespace and parser hints as well as execution related
        options.
    * - Completely arbitrary task function arguments (i.e. ``def mytask(any,
        thing, at, all)``)
      - Mixed
      - This gets its own line item because: Fabric-level task functions must
        now take a `.Connection` object as their first positional argument.
        (The rest of the function signature is, as before, totally up to the
        user & will get automatically turned into CLI flags.)

        This sacrifices a small bit of the "quick DSL" of v1 in exchange for a
        cleaner, easier to understand/debug, and more user-overrideable API
        structure.

        As a side effect, it lessens the distinction between "module of
        functions" and "class of methods"; users can more easily start with the
        former and migrate to the latter when their needs grow/change.
    * - Implicit task tree generation via import-crawling
      - Mixed
      - Namespace construction is now more explicit; for example, imported
        modules in your ``fabfile.py`` are no longer auto-scanned and
        auto-added to the task tree.

        However, the root ``fabfile.py`` *is* automatically loaded (using
        `Collection.from_module <invoke.collection.Collection.from_module>`),
        preserving the simple/common case. See :ref:`task-namespaces` for
        details.

        We may reinstate import (opt-in) module scanning later, since the use
        of explicit namespace objects still allows users control over the tree
        that results.

.. _upgrading-cli:

CLI arguments, options and behavior
-----------------------------------

.. list-table::
    :header-rows: 1
    :widths: 40 10 50

    * - Behavior
      - Status
      - Notes
    * - ``python -m fabric`` as stand-in for ``fab``
      - Pending
      - Should be trivial to port this over.
    * - ``-a``/``--no_agent``
      - Removed
      - To disable use of an agent permanently, set config value
        ``connect_kwargs.allow_agent`` to ``False``; to disable temporarily,
        unset the ``SSH_AUTH_SOCK`` env var.
    * - ``-I``/``--initial-password-prompt``
      - Ported
      - It's now :option:`--prompt-for-password` and/or
        :option:`--prompt-for-passphrase`, depending on whether you were using
        the former to fill in passwords or key passphrases (or both.)
    * - TODO: rest of this
      - Pending
      - Yup

.. _upgrading-commands:

Shell command execution (``local``/``run``/``sudo``)
----------------------------------------------------

.. list-table::
    :widths: 40 10 50

    * - ``local`` and ``run``/``sudo`` have wildly differing APIs and
        implementations
      - Removed
      - All command execution is now unified; all three functions (now
        methods on `.Connection`, though ``local`` is also available as
        `invoke.run` for standalone use) have the same underlying protocol and
        logic (the `~invoke.runners.Runner` class hierarchy), with only
        low-level details like process creation and pipe consumption differing.

        For example, in v1 ``local`` required you to choose between displaying
        and capturing subprocess output; v2's is like ``run`` and does both at
        the same time.
    * - ``local``
      - Ported
      - TK: Details specific to ``local``, including any of its args. Maybe
        make a table for each function with rows being args?
    * - ``run``
      - Ported
      - TK: see above.

        Also, there is no more built-in ``use_shell`` or ``shell`` option; the
        old "need" to wrap with an explicit shell invocation is no longer
        necessary or usually desirable. TODO: this isn't 100% true actually, it
        depends :(
    * - Prompt auto-response, via ``env.prompts`` and/or ``sudo``'s internals
      - Ported
      - The ``env.prompts`` functionality has been significantly fleshed out,
        into a framework of :ref:`Watchers <autoresponding>` which operate on
        any (local or remote!) running command's input and output streams.

        In addition, ``sudo`` has been rewritten to use that framework; while
        still useful enough to offer an implementation in core, it no longer
        does anything users cannot do themselves using public APIs.
    * - ``fabric.context_managers.cd``/``lcd`` (and ``prefix``) allow scoped
        mutation of executed comments
      - Mixed
      - These are now methods on `~invoke.context.Context` (`Context.cd
        <invoke.context.Context.cd>`, `Context.prefix
        <invoke.context.Context.prefix>`) but need work in its subclass
        `.Connection` (quite possibly including recreating ``lcd``) so that
        local vs remote state are separated.
    * - ``fabric.context_managers.shell_env`` and its specific expression
        ``path``, for modifying remote environment variables (locally, one
        would just modify `os.environ`.)
      - Ported
      - The context managers were the only way to set environment variables at
        any scope; in modern Fabric, subprocess shell environment is
        controllable per-call (directly in `.Connection.run` and siblings
        via an ``env`` kwarg) *and* across multiple calls (by manipulating the
        configuration system, statically or at runtime.)

    * - Controlling subprocess output & other activity display text by
        manipulating ``fabric.state.output`` (directly or via
        ``fabric.context_managers.hide``, ``show`` or ``quiet`` as well as the
        ``quiet`` kwarg to ``run``/``sudo``)
      - Mixed
      - The core concept of "output levels" is gone, likely to be replaced in
        the near term by a logging module (stdlib or other) which output levels
        poorly reimplemented.

        Command execution methods like `~invoke.runners.Runner.run` retain a
        ``hide`` kwarg controlling which subprocess streams are copied to your
        terminal, and an ``echo`` kwarg controlling whether commands are
        printed before execution. All of these also honor the configuration
        system.

.. _upgrading-utility:

Utilities
---------

.. list-table::
    :widths: 40 10 50

    * - Error handling via ``abort()`` and ``warn()``
      - Ported
      - The old functionality leaned too far in the "everything is a DSL"
        direction & didn't offer enough value to offset how it gets in the way
        of experienced Pythonistas.

        These functions have been removed in favor of "just raise an exception"
        (with one useful option being Invoke's `~invoke.exceptions.Exit`) as
        exception handling feels more Pythonic than thin wrappers around
        ``sys.exit`` or having to ``except SystemExit:`` and hope it was a
        `SystemExit` your own code raised!
    * - ANSI color helpers in ``fabric.colors`` allowed users to easily print
        ANSI colored text without a standalone library
      - Removed
      - There seemed no point to poorly replicating one of the many fine
        terminal-massaging libraries out there (such as those listed in the
        description of `#101 <https://github.com/fabric/fabric/issues/101>`_)
        in the rewrite, so we didn't.

        That said, it seems highly plausible we'll end up vendoring such a
        library in the future to offer internal color support, at which point
        "baked-in" color helpers would again be within easy reach.
    * - ``with char_buffered`` context manager for forcing a local stream to be
        character buffered
      - Ported
      - This is now `~invoke.terminals.character_buffered`.

.. _upgrading-networking:

Networking
----------

.. list-table::
    :widths: 40 10 50

    * - ``env.gateway`` for setting an SSH jump gateway
      - Ported
      - This is now the ``gateway`` kwarg to `.Connection`, and -- for the
        newly supported ``ProxyJump`` style gateways, which can be nested
        indefinitely! -- should be another `.Connection` object instead of a
        host string.

        (You may specify a runtime, non-SSH-config-driven
        ``ProxyCommand``-style string as the ``gateway`` kwarg instead, which
        will act just like a regular ``ProxyCommand``.)
    * - ``ssh_config``-driven ``ProxyCommand`` support
      - Ported
      - This continues to work as it did in v1.
    * - ``with remote_tunnel(...):`` port forwarding
      - Ported
      - This is now `.Connection.forward_local`, since it's used to *forward* a
        *local* port to the remote end. (New in v2 is the logical inverse,
        `.Connection.forward_remote`.)

Authentication
--------------

.. note::
    Some ``env`` keys from v1 were simply passthroughs to Paramiko's
    `SSHClient.connect <paramiko.client.SSHClient.connect>` method. Fabric 2
    gives you explicit control over the arguments it passes to that method, via
    the ``connect_kwargs`` :doc:`configuration </concepts/configuration>`
    subtree, and the below table will frequently refer you to that approach.

.. list-table::
    :widths: 40 10 50

    * - ``env.key_filename``
      - Ported
      - Use ``connect_kwargs``.
    * - ``env.password``
      - Ported
      - Use ``connect_kwargs``.

        Also note that this used to perform double duty as connection *and*
        sudo password; the latter is now found in the ``sudo.password``
        setting.
    * - ``env.gss_(auth|deleg|kex)``
      - Ported
      - Use ``connect_kwargs``.
    * - ``env.key``, a string or file object holding private key data, whose
        specific type is auto-determined and instantiated for use as the
        ``pkey`` connect kwarg
      - Removed
      - This has been dropped as unnecessary (& bug-prone) obfuscation of
        Paramiko-level APIs; users should already know which type of key
        they're dealing with and instantiate a ``PKey`` subclass themselves,
        placing the result in ``connect_kwargs.pkey``.
    * - ``env.no_agent``, simply a renaming/inversion of the ``allow_agent``
        connect kwarg
      - Ported
      - Users who were setting this to ``True`` should now simply set
        ``connect_kwargs.allow_agent`` to ``False`` instead.
    * - ``env.no_keys``, similar to ``no_agent``, just an inversion of
        the ``look_for_keys`` connect kwarg
      - Ported
      - Use ``connect_kwargs.look_for_keys`` instead (setting it to ``False``
        to disable Paramiko's default key-finding behavior.)
    * - ``env.passwords`` stores connection passwords in a dict keyed by host
        strings
      - Mixed
      - Each `.Connection` object may be configured with its own
        ``connect_kwargs`` given at instantiation time, allowing for per-host
        password configuration already.

        However, we expect users may want a simpler way to set configuration
        values that are turned into implicit `.Connection` objects
        automatically; such a feature is still pending.
    * - Configuring ``IdentityFile`` in one's ``ssh_config``
      - Ported
      - Still honored in v2, along with a bunch of newly honored ``ssh_config``
        settings; see :ref:`ssh-config`.

Configuration
-------------

In general, configuration has been massively improved over the old ``fabricrc``
files; most config logic comes from :ref:`Invoke's configuration system
<configuration>`, which offers a full-fledged configuration hierarchy (in-code
config, multiple config file locations, environment variables, CLI flags, and
more) and multiple file formats. Nearly all configuration avenues in Fabric 1
become, in v2, manipulation of whatever part of the config hierarchy is most
appropriate for your needs.

Fabric 2 itself only makes minor modifications to (or parameterizations of)
Invoke's setup; see :ref:`Fabric 2's specific config doc page
<fab-configuration>` for details.

.. note::
    Make sure to look elsewhere in this document for details on any given v1
    ``env`` setting, as many have moved outside the configuration system into
    object or method keyword arguments.

.. list-table::
    :widths: 40 10 50

    * - Modifying ``fabric.(api.)env`` directly
      - Ported
      - To effect truly global-scale config changes, use config files,
        task-collection-level config data, or the invoking shell's environment
        variables.
    * - Making locally scoped ``env`` changes via ``with settings(...):``
      - Mixed
      - Most of the use cases surrounding ``with settings`` are now served by
        the fact that `.Connection` objects keep per-host/connection state -
        the pattern of switching the implicit global context around was a
        design antipattern which is now gone.

        The remaining such use cases have been turned into context-manager
        methods of `.Connection` (or its parent class), or have such methods
        pending.
    * - SSH config file loading (off by default, limited to ``~/.ssh/config``
        only unless configured to a different, single path)
      - Ported
      - Much improved: SSH config file loading is **on** by default (which
        :ref:`can be changed <disabling-ssh-config>`), multiple sources are
        loaded and merged just like OpenSSH, and more besides; see
        :ref:`ssh-config`.

        In addition, we've added support for some ``ssh_config`` directives
        which were ignored by v1, such as ``ConnectTimeout`` and
        ``ProxyCommand``, and going forwards we intend to support as much of
        ``ssh_config`` as is reasonably possible.

.. _upgrading-env:

``fabric.env`` reference
------------------------

Many/most of the members in v1's ``fabric.env`` are covered in the above
per-topic sections; any that are *not* covered elsewhere, live here. All are
explicitly noted as ``env.<name>`` for ease of searching in your browser or
viewer.

.. list-table::
    :widths: 40 10 50

    * - ``env.roles``
      - Pending
      - As noted in :ref:`upgrading-api`, roles as a concept were ported to
        `.Group`, but there's no central clearinghouse in which to store them.

        We *may* delegate this to userland forever, but seems likely a
        common-best-practice option (such as creating `Groups <.Group>` from
        some configuration subtree and storing them as a
        `~invoke.context.Context` attribute) will appear in early 2.x.


Example upgrade process
=======================

This section goes over upgrading a small but nontrivial Fabric 1 fabfile to
work with Fabric 2. It's not meant to be exhaustive, merely illustrative; for a
full list of how to upgrade individual features or concepts, see the last
section, :ref:`upgrade-specifics`.

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
- `@task <invoke.tasks.task>`, as before, but coming from Invoke as it's not
  SSH-specific;
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
- That ``local()`` call is now a method call on the `.Connection`,
  `.Connection.local`.
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
`.Connection.local` is just a rebinding of `Context.run
<invoke.context.Context.run>`, Invoke's local subprocess execution method. Now
we get to the actual deploy step, which simply invokes `.Connection.run`
instead, executing remotely (on whichever host the `.Connection` has been bound
to).

``with cd()`` is not fully implemented for the remote side of things, but we
expect it will be soon. For now we fall back to command chaining with ``&&``.

::

    @task
    def deploy(c):
        code_dir = '/srv/django/myproject'
        if not c.run("test -d {}".format(code_dir), warn=True):
            cmd = "git clone user@vcshost:/path/to/repo/.git {}"
            c.run(cmd.format(code_dir))
        c.run("cd {} && git pull".format(code_dir))
        c.run("cd {} && touch app.wsgi".format(code_dir))

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
        c.run("cd {} && git pull".format(code_dir))
        c.run("cd {} && touch app.wsgi".format(code_dir))
