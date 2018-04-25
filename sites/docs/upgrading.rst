.. _upgrading:

=========================
Upgrading from Fabric 1.x
=========================

Modern Fabric (2+) represents a near-total reimplementation & reorganization of
the software. It's been :ref:`broken in two <invoke-split-from-fabric>`,
cleaned up, made more explicit, and so forth. In some cases, upgrading requires
only basic search & replace; in others, more work is needed.

If you read this document carefully, it should guide you in the right direction
until you're fully upgraded. Should anything be missing, please file a ticket
`on Github <https://github.com/fabric/fabric>`_ and we'll update it ASAP.


'Sidegrading' to Invoke
=======================

We linked to a note about this above, but to be explicit: modern Fabric is
really two separate libraries, and anything not strictly SSH or network related
has been :ref:`split out into the Invoke project <invoke-split-from-fabric>`.

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
modern Fabric that might make upgrading worth your time.

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

To help with gradual upgrades, modern Fabric may be installed under the name
``fabric2`` (in addition to being made available "normally" as versions 2.0+ of
``fabric``) and can live alongside installations of version 1.x.

Thus, if you have a large codebase and don't want to make the jump to modern
versions in one leap, it's possible to have both Fabric 1 (``fabric``, as you
presumably had it installed previously) and modern Fabric (as ``fabric2``)
resident in your Python environment simultaneously.

.. note::
    We strongly recommend that you eventually migrate all code using Fabric 1,
    to versions 2 or above, so that you can move back to installing and
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
features which haven't been implemented in modern versions yet.

Most sections are broken down in table form, as follows:

.. list-table::

    * - Fabric 1 feature or behavior
      - Status, see below for breakdown
      - Migration notes, removal rationale, etc

The 'status' field will be one of the following:

- **Ported**: available already, possibly renamed or moved (frequently, moved
  into the `Invoke <http://pyinvoke.org>`_ codebase.)
- **Pending**: would fit, but has not yet been ported, good candidate for a
  patch (but please check for a ticket first!)
- **Removed**: explicitly *not* ported (no longer fits with vision, had too
  poor a maintenance-to-value ratio, etc) and unlikely to be reinstated.
- **Mixed**: some combination of the above, such as a feature set that is
  partly ported and partly pending.

Here's a quick local table of contents for navigation purposes:

.. contents::
    :local:

General / conceptual
--------------------

- Modern Fabric is fully Python 3 compatible; as a cost, Python 2.5 support (a
  longstanding feature of Fabric 1) has been dropped - in fact, we've dropped
  support for anything older than Python 2.7.
- The CLI task-oriented workflow remains a primary design goal, but the library
  use case is no longer a second-class citizen; instead, the library
  functionality has been designed first, with the CLI/task features built on
  top of it.
- Additionally, within the CLI use case, version 1 placed too much emphasis on
  'lazy' interactive prompts for authentication secrets or even connection
  parameters, driven in part by a lack of strong configuration mechanisms. Over
  time it became clear this wasn't worth the tradeoffs of having confusing
  noninteractive behavior and difficult debugging/testing procedures.

  Modern Fabric takes an arguably cleaner approach (based on functionality
  added to v1 over time) where users are encouraged to leverage the
  configuration system and/or serve the user prompts for runtime secrets at the
  *start* of the process; if the system determines it's missing information
  partway through, it raises exceptions instead of prompting.
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
        call global methods which implicitly reference them
        (``run``/``sudo``/etc)
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
    * - ``@hosts`` and ``@roles`` for determining the default list of host or
        group-of-host targets a given task uses
      - Pending
      - These decorators were very much in the "DSL" vein of Fabric 1 and have
        not been prioritized for the rewrite, though they are likely to return
        in some form, and probably sooner instead of later.
    * - ``@serial``/``@parallel``/``@runs_once``
      - Mixed
      - Parallel execution is currently offered at the API level via `.Group`
        subclasses such as `.ThreadingGroup`; however, designating entire
        sessions and/or tasks to run in parallel (or to exempt from
        parallelism) has not been solved yet. The problem needs solving at a
        higher level than just SSH targets, as well (see e.g. `invoke#63
        <https://github.com/pyinvoke/invoke/issues/63>`_.)
    * - ``execute()`` for calling named tasks from other tasks while honoring
        decorators and other execution mechanics (as opposed to calling them
        simply as functions)
      - Pending
      - This is one of the top "missing features" from the rewrite; see
        `invoke#170 <https://github.com/pyinvoke/invoke/issues/170>`_ for
        details.
    * - ``Task`` class for programmatic creation of tasks (as opposed to using
        some function object and the ``@task`` decorator)
      - Ported
      - While not sharing many implementation details with v1, modern Fabric
        (via Invoke) has a publicly exposed `~invoke.tasks.Task` class, which
        alongside `~invoke.collection.Collection` allow full programmatic
        creation of task trees, no decorator needed.

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
        and capturing subprocess output; modern ``local`` is like ``run`` and
        does both at the same time.
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
        ``quiet`` kwarg to ``run``/``sudo``; plus
        ``utils.puts``/``fastprint``)
      - Mixed
      - The core concept of "output levels" is gone, likely to be replaced in
        the near term by a logging module (stdlib or other) which output levels
        poorly reimplemented.

        Command execution methods like `~invoke.runners.Runner.run` retain a
        ``hide`` kwarg controlling which subprocess streams are copied to your
        terminal, and an ``echo`` kwarg controlling whether commands are
        printed before execution. All of these also honor the configuration
        system.
    * - ``CommandTimeout`` raised when a command exceeded configured timeout
      - Pending
      - Command timeouts have not been ported yet, but will likely be added (at
        the Invoke layer) in future.

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
    * - ``docs.unwrap_tasks`` for extracting docstrings from wrapped task
        functions
      - Pending
      - This has not been ported yet, nor have we checked to see if it actually
        needs to be, but we suspect a new/ported version of it may be useful.
    * - ``network.normalize``/``denormalize``/``parse_host_string``, ostensibly
        internals but sometimes exposed to users for dealing with host strings
      - Removed
      - As with other host-string-related tools, these are gone and serve no
        purpose. `.Connection` is now the primary API focus and has individual
        attributes for all "host string" components.
    * - ``utils.indent`` for indenting/wrapping text (uncommonly used)
      - Pending
      - Not ported yet; ideally we'll just vendor a third party lib in Invoke.

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
        *local* port to the remote end. (Newly added is the logical inverse,
        `.Connection.forward_remote`.)
    * - ``NetworkError`` raised on some network related errors
      - Removed
      - In v1 this was simply a (partially implemented) stepping-back from the
        original "just sys.exit on any error!" behavior. Modern Fabric is
        significantly more exception-friendly; situations that would raise
        ``NetworkError`` in v1 now simply become the real underlying
        exceptions, typically from Paramiko or the stdlib.

Authentication
--------------

.. note::
    Some ``env`` keys from v1 were simply passthroughs to Paramiko's
    `SSHClient.connect <paramiko.client.SSHClient.connect>` method. Modern
    Fabric gives you explicit control over the arguments it passes to that
    method, via the ``connect_kwargs`` :doc:`configuration
    </concepts/configuration>` subtree, and the below table will frequently
    refer you to that approach.

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
      - Still honored, along with a bunch of newly honored ``ssh_config``
        settings; see :ref:`ssh-config`.

.. _upgrading-transfers:

File transfer
-------------

The below feature breakdown applies to the ``put`` and/or ``get`` "operation"
functions from v1.

.. list-table::
    :widths: 40 10 50

    * - Transferring individual files owned by the local and remote user
      - Ported
      - Basic file transfer in either direction works and is offered as
        `.Connection.get`/`.Connection.put` (though the code is split out
        into a separate-responsibility class, `.Transfer`.)

        The signature of these methods has been cleaned up compared to v1,
        though their positional-argument essence (``get(remote, local)`` and
        ``put(local, remote)`` remains the same.
    * - Omit the 'destination' argument for implicit 'relative to local
        context' behavior (e.g. ``put('local.txt')`` implicitly uploading to
        remote ``$HOME/local.txt``.)
      - Ported
      - You should probably still be explicit, because this is Python.
    * - Use either file paths *or* file-like objects on either side of
        the transfer operation (e.g. uploading a `StringIO` instead of an
        on-disk file)
      - Ported
      - This was a useful enough and simple enough trick to keep around.
    * - Preservation of source file mode at destination (e.g. ensuring an
        executable bit that would otherwise be dropped by the destination's
        umask, is re-added.)
      - Ported
      - Not only was this ported, but it is now the default behavior. It may be
        disabled via kwarg if desired.
    * - Bundled ``sudo`` operations as part of file transfer
      - Removed
      - This was one of the absolute buggiest parts of v1 and never truly did
        anything users could not do themselves with a followup call to
        ``sudo``, so we opted not to port it.

        Should enough users pine for its loss, we *may* reconsider, but if we
        do it will be with a serious eye towards simplification and/or an
        approach not involving intermediate files.
    * - Recursive multi-file transfer (e.g. ``put(a_directory)`` uploads entire
        directory and all its contents)
      - Removed
      - This was *another* one of the buggiest parts of v1, and over time it
        became clear that its maintenance burden far outweighed the fact that
        it was poorly reinventing ``rsync`` and/or the use of archival file
        tools like ye olde ``tar``+``gzip``.


.. _upgrading-configuration:

Configuration
-------------

In general, configuration has been massively improved over the old ``fabricrc``
files; most config logic comes from :ref:`Invoke's configuration system
<configuration>`, which offers a full-fledged configuration hierarchy (in-code
config, multiple config file locations, environment variables, CLI flags, and
more) and multiple file formats. Nearly all configuration avenues in Fabric 1
become, in modern Fabric, manipulation of whatever part of the config hierarchy
is most appropriate for your needs.

Modern versions of Fabric only make minor modifications to (or
parameterizations of) Invoke's setup; see :ref:`our locally-specific config doc
page <fab-configuration>` for details.

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
    * - Making locally scoped ``fabric.env`` changes via ``with
        settings(...):`` or its decorator equivalent, ``@with_settings``
      - Mixed
      - Most of the use cases surrounding ``settings()`` are now served by
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

.. _upgrading-contrib:

``contrib``
-----------

The old ``contrib`` module represented "best practice" functions that did not,
themselves, require core support from the rest of Fabric but were built using
the same primitives available to users.

In modern Fabric, that responsibility has been removed from the core library
into other standalone libraries which have their own identity & release
process, typically either `invocations
<https://github.com/pyinvoke/invocations>`_ (local-oriented code that does not
use SSH) or `patchwork <https://github.com/fabric/patchwork>`_ (remote-oriented
code.)

Those libraries are still a work in progress, not least because we still need
to identify the best way to bridge the gap between them (as many operations are
not intrinsically local-or-remote but can work on either end.)

Since they are by definition built on the core APIs available to all users,
they currently get less development focus; users can always implement their own
versions without sacrificing much (something less true for the core libraries.)
We expect to put more work into curating these collections once the core APIs
have settled down.

Details about what happened to each individual chunk of ``fabric.contrib`` are
in the below table:

.. list-table::
    :widths: 40 10 50

    * - ``console.confirm`` for easy bool-returning confirmation prompts
      - Ported
      - Moved to ``invocations.console.confirm``, with minor signature tweaks.
    * - ``django.*``, supporting integration with a local Django project re:
        importing and using Django models and other code
      - Removed
      - We aren't even sure if this is useful a decade after it was written,
        given how much Django has surely changed since then. If you're reading
        and are sad that this is gone, let us know!
    * - ``files.*`` (e.g. ``exists``, ``append``, ``contains`` etc) for
        interrogating and modifying remote files
      - Mixed
      - Many of the more useful functions in this file have been ported to
        ``patchwork.files`` but are still in an essentially alpha state.

        Others, such as ``is_link``, ``comment``/``uncomment``, etc have not
        been ported yet. If they are, the are likely to end up in the same
        place.

        Of note, even the ones that have been alpha-ported may be removed; for
        example, ``append`` is an antipattern (it's significantly safer and
        more maintainable to upload a rendered template or static file) and we
        don't wish to encourage those when possible.
    * - ``project.rsync_project`` for rsyncing the entire host project remotely
      - Ported
      - Now ``patchwork.transfers.rsync``, with some modifications.
    * - ``project.rsync_project`` for uploading host project via archive file
        and scp
      - Removed
      - This did not seem worth porting; the overall pattern of "copy my local
        bits remotely" is already arguably an antipattern (vs repeatable
        deploys of artifacts, or at least remote checkout of a VCS tag) and if
        one is going down that road anyways, rsync is a much smarter choice.

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
work with modern Fabric. It's not meant to be exhaustive, merely illustrative;
for a full list of how to upgrade individual features or concepts, see the last
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
- Result objects are pretty similar between versions; modern Fabric's results
  no longer pretend to "be" strings, but instead act more like booleans, acting
  truthy if the command exited cleanly, and falsey otherwise. In terms of
  attributes exhibited, most of the same info is available, in fact typically
  more in modern editions than in v1.
- ``abort()`` is gone; you should use exceptions or builtins like ``sys.exit``
  instead.

.. TODO: check up on modern-Fabric compatible patchwork for confirm()

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

Now we have the entire, upgraded fabfile that will work with modern Fabric::

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
