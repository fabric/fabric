.. _upgrading:

==================
Upgrading from 1.x
==================

Modern Fabric (2+) represents a near-total reimplementation & reorganization of
the software. It's been :ref:`broken in two <invoke-split-from-fabric>`,
cleaned up, made more explicit, and so forth. In some cases, upgrading requires
only basic search & replace; in others, more work is needed.

If you read this document carefully, it should guide you in the right direction
until you're fully upgraded. If any functionality you're using in Fabric 1
isn't listed here, please file a ticket `on Github
<https://github.com/fabric/fabric>`_ and we'll update it ASAP.

.. warning::
    As of the 2.0 release line, Fabric 2 is **not** at 100% feature parity with
    1.x! Some features have been explicitly dropped, but others simply have not
    been ported over yet, either due to time constraints or because said
    features need to be re-examined in a modern context.

    Please review the information below, including the :ref:`upgrade-specifics`
    section which contains a very detailed list, before filing bug reports!

    Also see :ref:`the roadmap <roadmap>` for additional notes about release
    versioning.

Why upgrade?
============

We'd like to call out, in no particular order, some specific improvements in
modern Fabric that might make upgrading worth your time.

.. note::
    These are all listed in the rest of the doc too, so if you're already sold,
    just skip there.

- Python 3 compatibility (specifically, we now support 2.7 and 3.4+);
- Thread-safe - no more requirement on multiprocessing for concurrency;
- API reorganized around `fabric.connection.Connection` objects instead of
  global module state;
- Command-line parser overhauled to allow for regular GNU/POSIX style flags and
  options on a per-task basis (no more ``fab mytask:weird=custom,arg=format``);
- Task organization is more explicit and flexible / has less 'magic';
- Tasks can declare other tasks to always be run before or after themselves;
- Configuration massively expanded to allow for multiple config files &
  formats, env vars, per-user/project/module configs, and much more;
- SSH config file loading enabled by default & has been fleshed out re:
  system/user/runtime file selection;
- Shell command execution API consistent across local and remote method calls -
  no more differentiation between ``local`` and ``run`` (besides where the
  command runs, of course!);
- Shell commands significantly more flexible re: interactive behavior,
  simultaneous capture & display (now applies to local subprocesses, not just
  remote), encoding control, and auto-responding;
- Use of Paramiko's APIs for the SSH layer much more transparent - e.g.
  `fabric.connection.Connection` allows control over the kwargs given to
  `SSHClient.connect <paramiko.client.SSHClient.connect>`;
- Gateway/jump-host functionality offers a ``ProxyJump`` style 'native' (no
  proxy-command subprocesses) option, which can be nested infinitely;


'Sidegrading' to Invoke
=======================

We linked to a note about this above, but to be explicit: modern Fabric is
really a few separate libraries, and anything not strictly SSH or network
related has been :ref:`split out into the Invoke project
<invoke-split-from-fabric>`.

This means that if you're in the group of users leveraging Fabric solely for
its task execution or ``local``, and never used ``run``, ``put`` or
similar - **you don't need to use Fabric itself anymore** and can simply
**'sidegrade' to Invoke instead**.

You'll still want to read over this document to get a sense of how things have
changed, but be aware that you can get away with ``pip install invoke`` and
won't need Fabric, Paramiko, cryptography dependencies, or anything else.


Using modern Fabric from within Invoke
======================================

We intend to enhance modern Fabric until it encompasses the bulk of Fabric 1's
use cases, such that you can use ``fab`` and fabfiles on their own without
caring too much about how it's built on top of Invoke.

However, prior to that point -- and very useful on its own for
intermediate-to-advanced users -- is the fact that modern Fabric is
designed with library or direct API use in mind. **It's entirely possible, and
in some cases preferable, to use Invoke for your CLI needs and Fabric as a pure
API within your Invoke tasks.**

In other words, you can eschew ``fab``/fabfiles entirely unless you find
yourself strongly needing the conveniences it wraps around ad-hoc sessions,
such as :option:`--hosts` and the like.


Running both Fabric versions simultaneously
===========================================

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

.. _from-v1:

Creating ``Connection`` and/or ``Config`` objects from v1 settings
------------------------------------------------------------------

A common tactic when upgrading piecemeal is to generate modern Fabric objects
whose contents match the current Fabric 1 environment. Whereas Fabric 1 stores
*all* configuration (including the "current host") in a single place -- the
``env`` object -- modern Fabric breaks things up into multiple (albeit
composed) objects: `~fabric.connection.Connection` for per-connection
parameters, and `~fabric.config.Config` for general settings and defaults.

In most cases, you'll only need to generate a `~fabric.connection.Connection`
object using the alternate class constructor `Connection.from_v1
<fabric.connection.Connection.from_v1>`, which should be fed your appropriate
local ``fabric.api.env`` object; see its API docs for details.

A contrived example::

    from fabric.api import env, run
    from fabric2 import Connection

    env.host_string = "admin@myserver"
    run("whoami") # v1
    cxn = Connection.from_v1(env)
    cxn.run("whoami") # v2+

By default, this constructor calls another API member -- `Config.from_v1
<fabric.config.Config.from_v1>` -- internally on your behalf. Users who need
tighter control over modern-style config options may opt to call that
classmethod explicitly and hand their modified result into `Connection.from_v1
<fabric.connection.Connection.from_v1>`, which will cause the latter to skip
any implicit config creation.

.. _v1-env-var-imports:

Mapping of v1 ``env`` vars to modern API members
------------------------------------------------

The ``env`` vars and how they map to `~fabric.connection.Connection` arguments
or `~fabric.config.Config` values (when fed into the ``.from_v1`` constructors
described above) are listed below.

.. list-table::
    :header-rows: 1

    * - v1 ``env`` var
      - v2+ usage (prefixed with the class it ends up in)

    * - ``always_use_pty``
      - Config: ``run.pty``.
    * - ``command_timeout``
      - Config: ``timeouts.command``; timeouts are now their own config
        subtree, whereas in v1 it was possible for the ambiguous ``timeout``
        setting -- see below -- to work for either connect OR command timeouts.
    * - ``forward_agent``
      - Config: ``connect_kwargs.forward_agent``.
    * - ``gateway``
      - Config: ``gateway``.
    * - ``host_string``
      - Connection: ``host`` kwarg (which can handle host-string like values,
        including user/port).
    * - ``key``
      - **Not supported**: Fabric 1 performed extra processing on this
        (trying a bunch of key classes to instantiate) before
        handing it into Paramiko; modern Fabric prefers to just let you handle
        Paramiko-level parameters directly.

        If you're filling your Fabric 1 ``key`` data from a file, we recommend
        switching to ``key_filename`` instead, which is supported.

        If you're loading key data from some other source as a string, you
        should know what type of key your data is and manually instantiate it
        instead, then supply it to the ``connect_kwargs`` parameter. For
        example::

            from io import StringIO  # or 'from StringIO' on Python 2
            from fabric.state import env
            from fabric2 import Connection
            from paramiko import RSAKey
            from somewhere import load_my_key_string

            pkey = RSAKey.from_private_key(StringIO(load_my_key_string()))
            cxn = Connection.from_v1(env, connect_kwargs={"pkey": pkey})

    * - ``key_filename``
      - Config: ``connect_kwargs.key_filename``.
    * - ``no_agent``
      - Config: ``connect_kwargs.allow_agent`` (inverted).
    * - ``password``
      - Config: ``connect_kwargs.password``, as well as ``sudo.password``
        **if and only if** the env's ``sudo_password`` (see below) is unset.
        (This mimics how v1 uses this particular setting - in earlier versions
        there was no ``sudo_password`` at all.)
    * - ``port``
      - Connection: ``port`` kwarg. Is casted to an integer due to Fabric 1's
        default being a string value (which is not valid in v2).

        .. note::
            Since v1's ``port`` is used both for a default *and* to store the
            current connection state, v2 uses it to fill in the Connection
            only, and not the Config, on assumption that it will typically be
            the current connection state.

    * - ``ssh_config_path``
      - Config: ``ssh_config_path``.
    * - ``sudo_password``
      - Config: ``sudo.password``.
    * - ``sudo_prompt``
      - Config: ``sudo.prompt``.
    * - ``timeout``
      - Config: ``timeouts.connection``, for connection timeouts, or
        ``timeouts.command`` for command timeouts (see above).
    * - ``use_ssh_config``
      - Config: ``load_ssh_configs``.
    * - ``user``
      - Connection: ``user`` kwarg.
    * - ``warn_only``
      - Config: ``run.warn``


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

Below are the typical values for the 'status' column, though some of them are a
bit loose - make sure to read the notes column in all cases! Also note that
things are not ironclad - eg any 'removed' item has some chance of returning if
enough users request it or use cases are made that workarounds are
insufficient.

- **Ported**: available already, possibly renamed or moved (frequently, moved
  into the `Invoke <http://pyinvoke.org>`_ codebase.)
- **Pending**: would fit, but has not yet been ported, good candidate for a
  patch. *These entries link to the appropriate Github ticket* - please do
  not make new ones!
- **Removed**: explicitly *not* ported (no longer fits with vision, had too
  poor a maintenance-to-value ratio, etc) and unlikely to be reinstated.

Here's a quick local table of contents for navigation purposes:

.. contents::
    :local:

.. _upgrading-general:

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
    * - Configure connection parameters globally (via ``env.host_string``,
        ``env.host``, ``env.port``, ``env.user``) and call global methods which
        implicitly reference them (``run``/``sudo``/etc)
      - Removed
      - The primary API is now properly OOP: instantiate
        `fabric.connection.Connection` objects and call their methods. These
        objects encapsulate all connection state (user, host, gateway, etc) and
        have their own SSH client instances.

        .. seealso::
            `Connection.from_v1 <fabric.connection.Connection.from_v1>`

    * - Emphasis on serialized "host strings" as method of setting user, host,
        port, etc
      - Ported/Removed
      - `fabric.connection.Connection` *can* accept a shorthand "host
        string"-like argument, but the primary API is now explicit user, host,
        port, etc keyword arguments.

        Additionally, many arguments/settings/etc that expected a host string
        in v1 will now expect a `fabric.connection.Connection` instance instead.
    * - Use of "roles" as global named lists of host strings
      - Ported
      - This need is now served by `fabric.group.Group` objects (which wrap
        some number of `fabric.connection.Connection` instances with "do a
        thing to all members" methods.) Users can create & organize these any
        way they want.

        See the line items for ``--roles`` (:ref:`upgrading-cli`),
        ``env.roles`` (:ref:`upgrading-env`) and ``@roles``
        (:ref:`upgrading-tasks`) for the status of those specifics.

.. _upgrading-tasks:

Task functions & decorators
---------------------------

.. note::
    Nearly all task-related functionality is implemented in Invoke; for more
    details see its :ref:`execution <invoking-tasks>` and :ref:`namespaces
    <task-namespaces>` documentation.

.. list-table::
    :widths: 40 10 50

    * - By default, tasks are loaded from a ``fabfile.py`` which is sought up
        towards filesystem root from the user's current working directory
      - Ported
      - This behavior is basically identical today, with minor modifications
        and enhancements (such as tighter control over the load process, and
        API hooks for implementing custom loader logic - see
        :ref:`loading-collections`.)
    * - "Classic" style implicit task functions lacking a ``@task`` decorator
      - Removed
      - These were on the way out even in v1, and arbitrary task/namespace
        creation is more explicitly documented now, via Invoke's
        `~invoke.tasks.Task` and `~invoke.collection.Collection`.
    * - "New" style ``@task``-decorated, module-level task functions
      - Ported
      - Largely the same, though now with superpowers - `@task
        <fabric.tasks.task>` can still be used without any parentheses, but
        where v1 only had a single ``task_class`` argument, the new version
        (largely based on Invoke's) has a number of namespace and parser hints,
        as well as execution related options (such as those formerly served by
        ``@hosts`` and friends).
    * - Arbitrary task function arguments (i.e. ``def mytask(any, thing, at,
        all)``)
      - Ported
      - This gets its own line item because: tasks must now take a
        `~invoke.context.Context` (vanilla Invoke) or
        `fabric.connection.Connection` (Fabric) object as their first
        positional argument. The rest of the function signature is, as before,
        totally up to the user & will get automatically turned into CLI flags.

        This sacrifices a small bit of the "quick DSL" of v1 in exchange for a
        cleaner, easier to understand/debug, and more user-overrideable API
        structure.

        As a side effect, it lessens the distinction between "module of
        functions" and "class of methods"; users can more easily start with the
        former and migrate to the latter when their needs grow/change.
    * - Implicit task tree generation via import-crawling
      - Ported/Removed
      - Namespace construction is now more explicit; for example, imported
        modules in your ``fabfile.py`` are no longer auto-scanned and
        auto-added to the task tree.

        However, the root ``fabfile.py`` *is* automatically loaded (using
        `Collection.from_module <invoke.collection.Collection.from_module>`),
        preserving the simple/common case. See :ref:`task-namespaces` for
        details.

        We may reinstate (in an opt-in fashion) imported module scanning later,
        since the use of explicit namespace objects still allows users control
        over the tree that results.
    * - ``@hosts`` for determining the default host or list of hosts a given
        task uses
      - Ported
      - Reinstated as the ``hosts`` parameter of `@task <fabric.tasks.task>`.
        Further, it can now handle dicts of `fabric.connection.Connection`
        kwargs in addition to simple host strings.
    * - ``@roles`` for determining the default list of group-of-host targets a
        given task uses
      - Pending
      - See :ref:`upgrading-api` for details on the overall 'roles' concept.
        When it returns, this will probably follow ``@hosts`` and become some
        ``@task`` argument.
    * - ``@serial``/``@parallel``/``@runs_once``
      - Ported/`Pending <https://github.com/pyinvoke/invoke/issues/63>`__
      - Parallel execution is currently offered at the API level via
        `fabric.group.Group` subclasses such as `fabric.group.ThreadingGroup`;
        however, designating entire sessions and/or tasks to run in parallel
        (or to exempt from parallelism) has not been solved yet.

        The problem needs solving at a higher level than just SSH targets, so
        this links to an Invoke-level ticket.
    * - ``execute`` for calling named tasks from other tasks while honoring
        decorators and other execution mechanics (as opposed to calling them
        simply as functions)
      - `Pending <https://github.com/pyinvoke/invoke/issues/170>`__
      - This is one of the top "missing features" from the rewrite; link is to
        Invoke's tracker.
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
    :widths: 40 10 50

    * - Exposure of task arguments as custom colon/comma delimited CLI
        arguments, e.g. ``fab mytask:posarg,kwarg=val``
      - Removed
      - CLI arguments are now proper GNU/POSIX-style long and short flags,
        including globbing shortflags together, space or equals signs to attach
        values, optional values, and much more. See :ref:`invoking-tasks`.
    * - Task definition names are mirrored directly on the command-line, e.g
        for task ``def journald_logs()``, command line argument is ``fab
        journald_logs``
      - Removed
      - Tasks names now get converted from underscores to hyphens. Eg. task
        ``def journald_logs()`` now evaluates to ``fab journald-logs`` on the
        commandline.
    * - Ability to invoke multiple tasks in a single command line, e.g. ``fab
        task1 task2``
      - Ported
      - Works great!
    * - ``python -m fabric`` as stand-in for ``fab``
      - Ported
      - Ported in 2.2.
    * - ``-a``/``--no_agent`` for disabling automatic SSH agent key selection
      - Removed
      - To disable use of an agent permanently, set config value
        ``connect_kwargs.allow_agent`` to ``False``; to disable temporarily,
        unset the ``SSH_AUTH_SOCK`` env var.
    * - ``-A``/``--forward-agent`` for enabling agent forwarding to the remote
        end
      - Removed
      - The config and kwarg versions of this are ported, but there is
        currently no CLI flag. Usual "you can set the config value at runtime
        with a shell env variable" clause is in effect, so this *may* not get
        ported, depending.
    * - ``--abort-on-prompts`` to turn interactive prompts into exceptions
        (helps avoid 'hanging' sessions)
      - Removed
      - See the notes about interactive prompts going away in
        :ref:`upgrading-general`. Without mid-session prompts, there's no need
        for this option.
    * - ``-c``/``--config`` for specifying an alternate config file path
      - Ported
      - ``--config`` lives on, but the short flag is now ``-f`` (``-c`` now
        determines which collection module name is sought by the task loader.)
    * - ``--colorize-errors`` (and ``env.colorize_errors``) to enable ANSI
        coloring of error output
      - `Pending <https://github.com/fabric/fabric/issues/101>`__
      - Very little color work has been done yet and this is one of the
        potentially missing pieces. We're unsure how often this was used in v1
        so it's possible it won't show up again, but generally, we like using
        color as an additional output vector, so...
    * - ``-d``/``--display`` for showing info on a given command
      - Ported
      - This is now the more standard ``-h``/``--help``, and can be given in
        either "direction": ``fab -h mytask`` or ``fab mytask -h``.
    * - ``-D``/``--disable-known-hosts`` to turn off Paramiko's automatic
        loading of user-level ``known_hosts`` files
      - `Pending <https://github.com/fabric/fabric/issues/1804>`__
      - Not ported yet, probably will be.
    * - ``-e``/``--eagerly-disconnect`` (and ``env.eagerly_disconnect``) which
        tells the execution system to disconnect from hosts as soon as a task
        is done running
      - Ported/`Pending <https://github.com/fabric/fabric/issues/1805>`__
      - There's no explicit connection cache anymore, so eager disconnection
        should be less necessary. However, investigation and potential feature
        toggles are still pending.
    * - ``-f``/``--fabfile`` to select alternate fabfile location
      - Ported
      - This is now split up into ``-c``/``--collection`` and
        ``-r``/``--search-root``; see :ref:`loading-collections`.
    * - ``-g``/``--gateway`` (and ``env.gateway``) for selecting a global SSH
        gateway host string
      - `Pending <https://github.com/fabric/fabric/issues/1806>`__
      - One can set the global ``gateway`` config option via an
        environment variable, which at a glance would remove the need for a
        dedicated CLI option. However, this approach only allows setting
        string values, which in turn only get used for ``ProxyCommand``
        style gatewaying, so it *doesn't* replace v1's ``--gateway``
        (which took a host string and turned it into a ``ProxyJump`` style
        gateway).

        Thus, if enough users notice the lack, we'll consider a feature-add
        that largely mimics the v1 behavior: string becomes first argument to
        `fabric.connection.Connection` and that resulting object is then set as
        ``gateway``.
    * - ``--gss-auth``/``--gss-deleg``/``--gss-kex``
      - Removed
      - These didn't seem used enough to be worth porting over, especially
        since they fall under the usual umbrella of "Paramiko-level connect
        passthrough" covered by the ``connect_kwargs`` config option. (Which,
        if necessary, can be set at runtime via shell environment variables,
        like any other config value.)
    * - ``--hide``/``--show`` for tweaking output display globally
      - Removed
      - This is configurable via the config system and env vars.
    * - ``-H``/``--hosts``
      - Ported
      - Works basically the same as before - if given, is shorthand for
        executing any given tasks once per host.
    * - ``-i`` for SSH key filename selection
      - Ported
      - Works same as v1, including ability to give multiple times to build a
        list of keys to try.
    * - ``-I``/``--initial-password-prompt`` for requesting an initial
        pre-execution password prompt
      - Ported
      - It's now :option:`--prompt-for-login-password`,
        :ref:`--prompt-for-sudo-password <prompt-for-sudo-password>` or
        :option:`--prompt-for-passphrase`, depending on whether you were using
        the former to fill in passwords or key passphrases (or both.)
    * - ``--initial-sudo-password-prompt`` for requesting an initial
        pre-execution sudo password prompt
      - Ported
      - This is now :option:`--prompt-for-sudo-password`. Still a bit of a
        mouthful but still 4 characters shorter!
    * - ``-k``/``--no-keys`` which prevents Paramiko's automatic loading of key
        files such as ``~/.ssh/id_rsa``
      - Removed
      - Use environment variables to set the ``connect_kwargs.look_for_keys``
        config value to ``False``.
    * - ``--keepalive`` for setting network keepalive
      - `Pending <https://github.com/fabric/fabric/issues/1807>`__
      - Not ported yet.
    * - ``-l``/``--list`` for listing tasks, plus ``-F``/``--list-format`` for
        tweaking list display format
      - Ported
      - Now with bonus JSON list-format! Which incidentally replaces ``-F
        short``/``--shortlist``.
    * - ``--linewise`` for buffering output line by line instead of roughly
        byte by byte
      - Removed
      - This doesn't really fit with the way modern command execution code
        views the world, so it's gone.
    * - ``-n``/``--connection-attempts`` controlling multiple connect retries
      - `Pending <https://github.com/fabric/fabric/issues/1808>`__
      - Not ported yet.
    * - ``--no-pty`` to disable automatic PTY allocation in ``run``, etc
      - Ported
      - Is now ``-p``/``--pty`` as the default behavior was switched around.
    * - ``--password``/``--sudo-password`` for specifying login/sudo password
        values
      - Removed
      - This is typically not very secure to begin with, and there are now many
        other avenues for setting the related configuration values, so
        they're gone at least for now.
    * - ``-P``/``--parallel`` for activating global parallelism
      - `Pending <https://github.com/pyinvoke/invoke/issues/63>`__
      - See the notes around ``@parallel`` in :ref:`upgrading-tasks`.
    * - ``--port`` to set default SSH port
      - Removed
      - Our gut says this is best left up to the configuration system's env var
        layer, or use of the ``port`` kwarg on `fabric.connection.Connection`;
        however it may find its way back.
    * - ``r``/``--reject-unknown-hosts`` to modify Paramiko known host behavior
      - `Pending <https://github.com/fabric/fabric/issues/1804>`__
      - Not ported yet.
    * - ``-R``/``--roles`` for global list-of-hosts target selection
      - `Pending <https://github.com/fabric/fabric/issues/1594>`__
      - As noted under :ref:`upgrading-api`, role lists are only partially
        applicable to the new API and we're still feeling out whether/how they
        would work at a global or CLI level.
    * - ``--set key=value`` for setting ``fabric.state.env`` vars at runtime
      - Removed
      - This is largely obviated by the new support for shell environment
        variables (just do ``INVOKE_KEY=value fab mytask`` or similar), though
        it's remotely possible a CLI flag method of setting config values will
        reappear later.
    * - ``-s``/``--shell`` to override default shell path
      - Removed
      - Use the configuration system for this.
    * - ``--shortlist`` for short/computer-friendly list output
      - Ported
      - See ``--list``/``--list-format`` - there's now a JSON format instead.
        No point reinventing the wheel.
    * - ``--skip-bad-hosts`` (and ``env.skip_bad_hosts``) to bypass problematic
        hosts
      - `Pending <https://github.com/fabric/fabric/issues/1809>`__
      - Not ported yet.
    * - ``--skip-unknown-tasks`` and ``env.skip_unknown_tasks`` for silently
        skipping past bogus task names on CLI invocation
      - Removed
      - This felt mostly like bloat to us and could require nontrivial parser
        changes to reimplement, so it's out for now.
    * - ``--ssh-config-path`` and ``env.ssh_config_path`` for selecting an SSH
        config file
      - Ported
      - This is now ``-S``/``--ssh-config``.
    * - ``--system-known-hosts`` to trigger loading systemwide ``known_hosts``
        files
      - `Pending <https://github.com/fabric/fabric/issues/1804>`__/Removed
      - This isn't super likely to come back as its own CLI flag but it may
        well return as a configuration value.
    * - ``-t``/``--timeout`` controlling connection timeout
      - Ported
      - It's now ``-t``/``--connect-timeout`` as ``--timeout`` was technically
        ambiguous re: connect vs command timeout.
    * - ``-T``/``--command-timeout``
      - Ported
      - Implemented in Invoke and preserved in ``fab`` under the same name.
    * - ``-u``/``--user`` to set global default username
      - Removed
      - Most of the time, configuration (env vars for true runtime, or eg
        user/project level config files as appropriate) should be used for
        this, but it may return.
    * - ``-w``/``--warn-only`` to toggle warn-vs-abort behavior
      - Ported
      - Ported as-is, no changes.
    * - ``-x``/``--exclude-hosts`` (and ``env.exclude_hosts``) for excluding
        otherwise selected targets
      - `Pending <https://github.com/fabric/fabric/issues/1594>`__
      - Not ported yet, is pending an in depth rework of global (vs
        hand-instantiated) connection/group selection.
    * - ``-z``/``--pool-size`` for setting parallel-mode job queue pool size
      - Removed
      - There's no job queue anymore, or at least at present. Whatever replaces
        it (besides the already-implemented threading model) is likely to look
        pretty different.

.. _upgrading-commands:

Shell command execution (``local``/``run``/``sudo``)
----------------------------------------------------

General
~~~~~~~

Behaviors shared across either ``run``/``sudo``, or all of
``run``/``sudo``/``local``. Subsequent sections go into per-function
differences.

.. list-table::
    :widths: 40 10 50

    * - ``local`` and ``run``/``sudo`` have wildly differing APIs and
        implementations
      - Removed
      - All command execution is now unified; all three functions (now
        methods on `fabric.connection.Connection`, though ``local`` is also
        available as `invoke.run` for standalone use) have the same underlying
        protocol and logic (the `~invoke.runners.Runner` class hierarchy), with
        only low-level details like process creation and pipe consumption
        differing.

        For example, in v1 ``local`` required you to choose between displaying
        and capturing subprocess output; modern ``local`` is like ``run`` and
        does both at the same time.
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
      - Ported/`Pending <https://github.com/fabric/fabric/issues/1752>`__
      - These are now methods on `~invoke.context.Context` (`Context.cd
        <invoke.context.Context.cd>`, `Context.prefix
        <invoke.context.Context.prefix>`) but need work in its subclass
        `fabric.connection.Connection` (quite possibly including recreating
        ``lcd``) so that local vs remote state are separated.
    * - ``fabric.context_managers.shell_env`` and its specific expression
        ``path`` (plus ``env.shell_env``, ``env.path`` and
        ``env.path_behavior``), for modifying remote environment variables
        (locally, one would just modify `os.environ`.)
      - Ported
      - The context managers were the only way to set environment variables at
        any scope; in modern Fabric, subprocess shell environment is
        controllable per-call (directly in `fabric.connection.Connection.run`
        and siblings via an ``env`` kwarg) *and* across multiple calls (by
        manipulating the configuration system, statically or at runtime.)
    * - Controlling subprocess output & other activity display text by
        manipulating ``fabric.state.output`` (directly or via
        ``fabric.context_managers.hide``, ``show`` or ``quiet`` as well as the
        ``quiet`` kwarg to ``run``/``sudo``; plus
        ``utils.puts``/``fastprint``)
      - Ported/`Pending <https://github.com/pyinvoke/invoke/issues/15>`__
      - The core concept of "output levels" is gone, likely to be replaced in
        the near term by a logging module (stdlib or other) which output levels
        poorly reimplemented.

        Command execution methods like `~invoke.runners.Runner.run` retain a
        ``hide`` kwarg controlling which subprocess streams are copied to your
        terminal, and an ``echo`` kwarg controlling whether commands are
        printed before execution. All of these also honor the configuration
        system.
    * - ``timeout`` kwarg and the ``CommandTimeout`` exception raised when said
        command-runtime timeout was violated
      - Ported
      - Primarily lives at the Invoke layer now, but applies to all command
        execution, local or remote; see the ``timeout`` argument to
        `~invoke.runners.Runner.run` and its related configuration value and
        CLI flag.
    * - ``pty`` kwarg and ``env.always_use_pty``, controlling whether commands
        run in a pseudo-terminal or are invoked directly
      - Ported
      - This has been thoroughly ported (and its behavior often improved)
        including preservation of the ``pty`` kwarg and updating the config
        value to be simply ``run.pty``. However, a major change is that pty
        allocation is now ``False`` by default instead of ``True``.

        Fabric 0.x and 1.x already changed this value around; during Fabric 1's
        long lifetime it became clear that neither default works for all or
        even most users, so we opted to return the default to ``False`` as it's
        cleaner and less wasteful.
    * - ``combine_stderr`` (kwarg and ``env.combine_stderr``) controlling
        whether Paramiko weaves remote stdout and stderr into the stdout stream
      - Removed
      - This wasn't terrifically useful, and often caused conceptual problems
        in tandem with ``pty`` (as pseudo-terminals by their nature always
        combine the two streams.)

        We recommend users who really need both streams to be merged, either
        use shell redirection in their command, or set ``pty=True``.
    * - ``warn_only`` kwarg for preventing automatic abort on non-zero return
        codes
      - Ported
      - This is now just ``warn``, both kwarg and config value. It continues to
        default to ``False``.
    * - ``stdout`` and ``stderr`` kwargs for reassigning default stdout/err
        mirroring targets, which otherwise default to the appropriate `sys`
        members
      - Ported
      - These are now ``out_stream`` and ``err_stream`` but otherwise remain
        similar in nature. They are also accompanied by the new, rather obvious
        in hindsight ``in_stream``.
    * - ``capture_buffer_size`` arg & use of a ring buffer for storing captured
        stdout/stderr to limit total size
      - `Pending <https://github.com/pyinvoke/invoke/issues/344>`__
      - Existing `~invoke.runners.Runner` implementation uses regular lists for
        capture buffers, but we fully expect to upgrade this to a ring buffer
        or similar at some point.
    * - Return values are string-like objects with extra attributes like
        ``succeeded`` and ``return_code`` sprinkled on top
      - Ported
      - Return values are no longer string-a-likes with a semi-private API, but
        are full fledged regular objects of type `~invoke.runners.Result`. They
        expose all of the same info as the old "attribute strings", and only
        really differ in that they don't pretend to be strings themselves.

        They do, however, still behave as booleans - just ones reflecting the
        exit code's relation to zero instead of whether there was any stdout.
    * - ``open_shell`` for obtaining interactive-friendly remote shell sessions
        (something that ``run`` historically was bad at )
      - Ported
      - Technically "removed", but only because the new version of
        ``run`` is vastly improved and can deal with interactive sessions at
        least as well as the old ``open_shell`` did, if not moreso.
        ``c.run("/my/favorite/shell", pty=True)`` should be all you need.

``run``
~~~~~~~

.. list-table::
    :widths: 40 10 50

    * - ``shell`` / ``env.use_shell`` designating whether or not to wrap
        commands within an explicit call to e.g. ``/bin/sh -c "real command"``;
        plus their attendant options like ``shell_escape``
      - Removed
      - Non-``sudo`` remote execution never truly required an explicit shell
        wrapper: the remote SSH daemon hands your command string off to the
        connecting user's login shell in almost all cases. Since wrapping is
        otherwise extremely error-prone and requires frustrating escaping
        rules, we dropped it for this use case.

        See the matching line items for ``local`` and ``sudo`` as their
        situations differ. (For now, because they all share the same
        underpinnings, `fabric.connection.Connection.run` does accept a
        ``shell`` kwarg - it just doesn't do anything with it.)

``sudo``
~~~~~~~~

Unless otherwise noted, all common ``run``+``sudo`` args/functionality (e.g.
``pty``, ``warn_only`` etc) are covered above in the section on ``run``; the
below are ``sudo`` specific.

.. list-table::
    :widths: 40 10 50

    * - ``shell`` / ``env.use_shell`` designating whether or not to wrap
        commands within an explicit call to e.g. ``/bin/sh -c "real command"``
      - `Pending <https://github.com/pyinvoke/invoke/issues/459>`__/Removed
      - See the note above under ``run`` for details on shell wrapping
        as a general strategy; unfortunately for ``sudo``, some sort of manual
        wrapping is still necessary for nontrivial commands (i.e. anything
        using actual shell syntax as opposed to a single program's argv) due to
        how the command string is handed off to the ``sudo`` program.

        We hope to upgrade ``sudo`` soon so it can perform a common-best-case,
        no-escaping-required shell wrapping on your behalf; see the 'Pending'
        link.
    * - ``user`` argument (and ``env.sudo_user``) allowing invocation via
        ``sudo -u <user>`` (instead of defaulting to root)
      - Ported
      - This is still here, and still called ``user``.
    * - ``group`` argument controlling the effective group of the sudo'd
        command
      - `Pending <https://github.com/pyinvoke/invoke/issues/540>`__
      - This has not been ported yet.

``local``
~~~~~~~~~

See the 'general' notes at top of this section for most details about the new
``local``. A few specific extras are below.

.. list-table::
    :widths: 40 10 50

    * - ``shell`` kwarg designating which shell to ask `subprocess.Popen` to
        use
      - Ported
      - Basically the same as in v1, though there are now situations where
        `os.execve` (or similar) is used instead of `subprocess.Popen`.
        Behavior is much the same: no shell wrapping (as in legacy ``run``),
        just informing the operating system what actual program to run.

.. _upgrading-utility:

Utilities
---------

.. list-table::
    :widths: 40 10 50

    * - Error handling via ``abort`` and ``warn``
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
      - Ported
      - v1 required using a Fabric-specific 'unwrap_tasks' helper function
        somewhere in your Sphinx build pipeline; now you can instead just
        enable the new `invocations.autodoc
        <http://invocations.readthedocs.io/en/latest/api/autodoc.html>`_ Sphinx
        mini-plugin in your extensions list; see link for details.
    * - ``network.normalize``, ``denormalize`` and ``parse_host_string``,
        ostensibly internals but sometimes exposed to users for dealing with
        host strings
      - Removed
      - As with other host-string-related tools, these are gone and serve no
        purpose. `fabric.connection.Connection` is now the primary API focus
        and has individual attributes for all "host string" components.
    * - ``utils.indent`` for indenting/wrapping text (uncommonly used)
      - Pending
      - Not ported yet; ideally we'll just vendor a third party lib in Invoke.
    * - ``reboot`` for rebooting and reconnecting to a remote system
      - Removed
      - No equivalent has been written for modern Fabric; now that the
        connection/client objects are made explicit, one can simply
        instantiate a new object with the same parameters (potentially with
        sufficient timeout parameters to get past the reboot, if one doesn't
        want to manually call something like `time.sleep`.)

        There is a small chance it will return if there appears to be enough
        need; if so, it's likely to be a more generic reconnection related
        `fabric.connection.Connection` method, where the user is responsible
        for issuing the restart shell command via ``sudo`` themselves.
    * - ``require`` for ensuring certain key(s) in ``env`` have values set,
        optionally by noting they can be ``provided_by=`` a list of setup tasks
      - Removed
      - This has not been ported, in part because the maintainers never used it
        themselves, and is unlikely to be directly reimplemented. However, its
        core use case of "require certain data to be available to run a given
        task" may return within the upcoming dependency framework.
    * - ``prompt`` for prompting the user & storing the entered data
        (optionally with validation) directly into ``env``
      - Removed
      - Like ``require``, this seemed like a less-used feature (especially
        compared to its sibling ``confirm``) and was not ported. If it returns
        it's likely to be via ``invocations``, which is where ``confirm`` ended
        up.

.. _upgrading-networking:

Networking
----------

.. list-table::
    :widths: 40 10 50

    * - ``env.gateway`` for setting an SSH jump gateway
      - Ported
      - This is now the ``gateway`` kwarg to `fabric.connection.Connection`,
        and -- for the newly supported ``ProxyJump`` style gateways, which can
        be nested indefinitely! -- should be another
        `fabric.connection.Connection` object instead of a host string.

        (You may specify a runtime, non-SSH-config-driven
        ``ProxyCommand``-style string as the ``gateway`` kwarg instead, which
        will act just like a regular ``ProxyCommand``.)
    * - ``ssh_config``-driven ``ProxyCommand`` support
      - Ported
      - This continues to work as it did in v1.
    * - ``with remote_tunnel(...):`` port forwarding
      - Ported
      - This is now `fabric.connection.Connection.forward_local`, since it's
        used to *forward* a *local* port to the remote end. (Newly added is the
        logical inverse, `fabric.connection.Connection.forward_remote`.)
    * - ``NetworkError`` raised on some network related errors
      - Removed
      - In v1 this was simply a (partially implemented) stepping-back from the
        original "just sys.exit on any error!" behavior. Modern Fabric is
        significantly more exception-friendly; situations that would raise
        ``NetworkError`` in v1 now simply become the real underlying
        exceptions, typically from Paramiko or the stdlib.
    * - ``env.keepalive`` for setting network keepalive value
      - `Pending <https://github.com/fabric/fabric/issues/1807>`__
      - Not ported yet.
    * - ``env.connection_attempts`` for setting connection retries
      - `Pending <https://github.com/fabric/fabric/issues/1808>`__
      - Not ported yet.
    * - ``env.timeout`` for controlling connection (and sometimes command
        execution) timeout
      - Ported
      - Connection timeout is now controllable both via the configuration
        system (as ``timeouts.connect``) and a direct kwarg on
        `fabric.connection.Connection`. Command execution timeout is its own
        setting now, ``timeouts.command`` and a ``timeout`` kwarg to ``run``
        and friends.

Authentication
--------------

.. note::
    Some ``env`` keys from v1 were simply passthroughs to Paramiko's
    `SSHClient.connect <paramiko.client.SSHClient.connect>` method. Modern
    Fabric gives you explicit control over the arguments it passes to that
    method, via the ``connect_kwargs`` :ref:`configuration <fab-configuration>`
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
    * - ``env.no_agent``, which is a renaming/inversion of Paramiko's
        ``allow_agent`` connect kwarg
      - Ported
      - Users who were setting this to ``True`` should now simply set
        ``connect_kwargs.allow_agent`` to ``False`` instead.
    * - ``env.no_keys``, similar to ``no_agent``, just an inversion of the
        ``look_for_keys`` connect kwarg
      - Ported
      - Use ``connect_kwargs.look_for_keys`` instead (setting it to ``False``
        to disable Paramiko's default key-finding behavior.)
    * - ``env.passwords`` (and ``env.sudo_passwords``) stores connection/sudo
        passwords in a dict keyed by host strings
      - Ported/`Pending <https://github.com/fabric/fabric/issues/4>`__
      - Each `fabric.connection.Connection` object may be configured with its
        own ``connect_kwargs`` given at instantiation time, allowing for
        per-host password configuration already.

        However, we expect users may want a simpler way to set configuration
        values that are turned into implicit `fabric.connection.Connection`
        objects automatically; such a feature is still pending.
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
        `fabric.connection.Connection.get`/`fabric.connection.Connection.put`
        (though the code is split out into a separate-responsibility class,
        `fabric.transfer.Transfer`.)

        The signature of these methods has been cleaned up compared to v1,
        though their positional-argument essence (``get(remote, local)`` and
        ``put(local, remote)`` remains the same.
    * - Omit the 'destination' argument for implicit 'relative to local
        context' behavior (e.g. ``put("local.txt")`` implicitly uploading to
        remote ``$HOME/local.txt``.)
      - Ported
      - You should probably still be explicit, because this is Python.
    * - Use either file paths *or* file-like objects on either side of
        the transfer operation (e.g. uploading a ``StringIO`` instead of an
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

        For one potential workaround, see the ``rsync`` function in `patchwork
        <https://github.com/fabric/patchwork>`_.
    * - Remote file path tilde expansion
      - Removed
      - This behavior is ultimately unnecessary (one can simply leave the
        tilde off for the same result) and had a few pernicious bugs of its
        own, so it's gone.
    * - Naming downloaded files after some aspect of the remote destination, to
        avoid overwriting during multi-server actions
      - Ported
      - Added back (to `fabric.transfer.Transfer.get`) in Fabric 2.6.


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
      - Ported/Pending
      - Most of the use cases surrounding ``settings`` are now served by
        the fact that `fabric.connection.Connection` objects keep
        per-host/connection state - the pattern of switching the implicit
        global context around was a design antipattern which is now gone.

        The remaining such use cases have been turned into context-manager
        methods of `fabric.connection.Connection` (or its parent class), or
        have such methods pending.
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
use SSH) or `patchwork <https://github.com/fabric/patchwork>`_ (primarily
remote-oriented code, though anything not explicitly dealing with both ends of
the connection will work just as well locally.)

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
      - Ported/Pending
      - Many of the more useful functions in this file have been ported to
        ``patchwork.files`` but are still in an essentially alpha state.

        Others, such as ``is_link``, ``comment``/``uncomment``, etc have not
        been ported yet. If they are, the are likely to end up in the same
        place.
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

A small handful of env vars were never publicly documented & were thus
implicitly private; those are not represented here.

.. list-table::
    :widths: 40 10 50

    * - ``env.abort_exception`` for setting which exception is used to abort
      - Removed
      - Aborting as a concept is gone, just raise whatever exception seems most
        reasonable to surface to an end user, or use `~invoke.exceptions.Exit`.
        See also :ref:`upgrading-utility`.
    * - ``env.all_hosts`` and ``env.tasks`` listing execution targets
      - Ported/`Pending <https://github.com/pyinvoke/invoke/issues/443>`__
      - Fabric's `~invoke.executor.Executor` subclass stores references to all
        CLI parsing results (including the value of :option:`--hosts`, the
        tasks requested and their args, etc) and the intent is for users to
        have access to that information.

        However, the details for that API (e.g. exposing the executor via a
        task's `~invoke.context.Context`/`fabric.connection.Connection`) are
        still in flux.
    * - ``env.command`` noting currently executing task name (in hindsight,
        quite the misnomer...)
      - Ported/`Pending <https://github.com/pyinvoke/invoke/issues/443>`__
      - See the notes for ``env.all_hosts`` above - same applies here re: user
        visibility into CLI parsing results.
    * - ``env.command_prefixes`` for visibility into (arguably also mutation
        of) the shell command prefixes to be applied to ``run``/``sudo``
      - Ported
      - This is now `~invoke.context.Context.command_prefixes`.
    * - ``env.cwd`` noting current intended working directory
      - Ported
      - This is now `~invoke.context.Context.command_cwds` (a list, not a
        single string, to more properly model the intended
        contextmanager-driven use case.)

        Note that remote-vs-local context for this data isn't yet set up; see
        the notes about ``with cd`` under :ref:`upgrading-commands`.
    * - ``env.dedupe_hosts`` controlling whether duplicate hosts in merged host
        lists get deduplicated or not
      - `Pending <https://github.com/fabric/fabric/issues/1594>`__
      - Not ported yet, will probably get tackled as part of roles/host lists
        overhaul.
    * - ``env.echo_stdin`` (undocumented) for turning off the default echoing
        of standard input
      - Ported
      - Is now a config option under the ``run`` tree, with much the same
        behavior.
    * - ``env.local_user`` for read-only access to the discovered local
        username
      - Removed
      - We're not entirely sure why v1 felt this was worth caching in the
        config; if you need this info, just import and call
        `fabric.util.get_local_user`.
    * - ``env.output_prefix`` determining whether or not line-by-line
        host-string prefixes are displayed
      - `Pending <https://github.com/pyinvoke/invoke/issues/15>`__
      - Differentiating parallel stdout/err is still a work in progress; we may
        end up reusing line-by-line logging and prefixing (ideally via actual
        logging) or we may try for something cleaner such as streaming to
        per-connection log files.
    * - ``env.prompts`` controlling prompt auto-response
      - Ported
      - Prompt auto-response is now publicly implemented as the
        `~invoke.watchers.StreamWatcher` and `~invoke.watchers.Responder` class
        hierarchy, instances of which can be handed to ``run`` via kwarg or
        stored globally in the config as ``run.watchers``.
    * - ``env.real_fabfile`` storing read-only fabfile path which was loaded by
        the CLI machinery
      - Ported
      - The loaded task `~invoke.collection.Collection` is stored on both the
        top level `~invoke.program.Program` object as well as the
        `~invoke.executor.Executor` which calls tasks; and
        `~invoke.collection.Collection` has a ``loaded_from`` attribute with
        this information.
    * - ``env.remote_interrupt`` controlling how interrupts (i.e. a local
        `KeyboardInterrupt` are caught, forwarded or other
      - Ported/Removed
      - Invoke's interrupt capture behavior is currently "always just send the
        interrupt character to the subprocess and continue", allowing
        subprocesses to handle ``^C`` however they need to, which is an
        improvement over Fabric 1 and roughly equivalent to setting
        ``env.remote_interrupt = True``.

        Allowing users to change this behavior via config is not yet
        implemented, and may not be, depending on whether anybody needs it - it
        was added as an option in v1 for backwards compat reasons.

        It is also technically possible to change interrupt behavior by
        subclassing and overriding `invoke.runners.Runner.send_interrupt`.
    * - ``env.roles``, ``env.roledefs`` and ``env.effective_roles``
        controlling/exposing what roles are available or currently in play
      - `Pending <https://github.com/fabric/fabric/issues/1594>`__
      - As noted in :ref:`upgrading-api`, roles as a concept were ported to
        `fabric.group.Group`, but there's no central clearinghouse in which to
        store them.

        We *may* delegate this to userland forever, but seems likely a
        common-best-practice option (such as creating `Groups
        <fabric.group.Group>` from some configuration subtree and storing them
        as a `~invoke.context.Context` attribute) will appear in early 2.x.
    * - ``env.ok_ret_codes`` for overriding the default "0 good, non-0 bad"
        error detection for subprocess commands
      - `Pending <https://github.com/pyinvoke/invoke/issues/541>`__
      - Not ported yet, but should involve some presumably minor updates to
        `invoke.runners.Runner.generate_result` and `~invoke.runners.Result`.
    * - ``env.sudo_prefix`` determining the sudo binary name + its flags used
        when creating ``sudo`` command strings
      - `Pending <https://github.com/pyinvoke/invoke/issues/540>`__
      - Sudo command construction does not currently look at the config for
        anything but the actual sudo prompt.
    * - ``env.sudo_prompt`` for setting the prompt string handed to ``sudo``
        (and then expected in return for auto-replying with a configured
        password)
      - Ported
      - Is now ``sudo.prompt`` in the configuration system.
    * - ``env.use_exceptions_for`` to note which actions raise exceptions
      - Removed
      - As with most other functionality surrounding Fabric 1's "jump straight
        to `sys.exit`" design antipattern, this is gone - modern Fabric will
        not be hiding any exceptions from user-level code.
    * - ``env.use_ssh_config`` to enable off-by-default SSH config loading
      - Ported
      - SSH config loading is now on by default, but an option remains to
        disable it. See :ref:`upgrading-configuration` for more.
    * - ``env.version`` exposing current Fabric version number
      - Removed
      - Just ``import fabric`` and reference ``fabric.__version__`` (string) or
        ``fabric.__version_info__`` (tuple).


Example upgrade process
=======================

This section goes over upgrading a small but nontrivial Fabric 1 fabfile to
work with modern Fabric. It's not meant to be exhaustive, merely illustrative;
for a full list of how to upgrade individual features or concepts, see
:ref:`upgrade-specifics`.

Sample original fabfile
-----------------------

Here's a (slightly modified to concur with 'modern' Fabric 1 best practices)
copy of Fabric 1's final tutorial snippet, which we will use as our test case
for upgrading::

    from fabric.api import abort, env, local, run, settings, task
    from fabric.contrib.console import confirm

    env.hosts = ["my-server"]

    @task
    def test():
        with settings(warn_only=True):
            result = local("./manage.py test my_app", capture=True)
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
        code_dir = "/srv/django/myproject"
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

In modern Fabric, we don't need to import nearly as many functions, due to the
emphasis on object methods instead of global functions. We only need the
following:

- `~invoke.exceptions.Exit`, a friendlier way of requesting a `sys.exit`;
- `@task <invoke.tasks.task>`, as before, but coming from Invoke as it's not
  SSH-specific;
- ``confirm``, which now comes from the Invocations library (also not
  SSH-specific; though Invocations is one of the descendants of
  ``fabric.contrib``, which no longer exists);

::

    from fabric import task
    from invoke import Exit
    from invocations.console import confirm

Host list
---------

The idea of a predefined *global* host list is gone; there is currently no
direct replacement. In general, users can set up their own execution context,
creating explicit `fabric.connection.Connection` and/or `fabric.group.Group`
objects as needed; core Fabric is in the process of building convenience
helpers on top of this, but "create your own Connections" will always be there
as a backstop.

Speaking of convenience helpers: most of the functionality of ``fab --hosts``
and ``@hosts`` has been ported over -- the former directly (see
:option:`--hosts`), the latter as a `@task <fabric.tasks.task>` keyword
argument. Thus, for now our example will be turning the global ``env.hosts``
into a lightweight module-level variable declaration, intended for use in the
subsequent calls to ``@task``::

    my_hosts = ["my-server"]

.. note::
    This is an area under active development, so feedback is welcomed.

.. TODO:
    - pre-task example
    - true baked-in default example (requires some sort of config hook)

Test task
---------

The first task in the fabfile uses a good spread of the API. We'll outline the
changes here (though again, all details are in :ref:`upgrade-specifics`):

- Declaring a function as a task is nearly the same as before: use a ``@task``
  decorator (which, in modern Fabric, can take more optional keyword arguments
  than its predecessor, including some which replace some of v1's decorators).
- ``@task``-wrapped functions must now take an explicit initial context
  argument, whose value will be a `fabric.connection.Connection` object at
  runtime.
- The use of ``with settings(warn_only=True)`` can be replaced by a simple
  kwarg to the ``local`` call.
- That ``local`` call is now a method call on the
  `fabric.connection.Connection`, `fabric.connection.Connection.local`.
- ``capture`` is no longer a useful argument; we can now capture and display at
  the same time, locally or remotely. If you don't actually *want* a local
  subprocess to mirror its stdout/err while it runs, you can simply say
  ``hide=True`` (or ``hide="stdout"`` or etc.)
- Result objects are pretty similar between versions; modern Fabric's results
  no longer pretend to "be" strings, but instead act more like booleans, acting
  truthy if the command exited cleanly, and falsey otherwise. In terms of
  attributes exhibited, most of the same info is available, and more besides.
- ``abort`` is gone; you should use whatever exceptions you feel are
  appropriate, or `~invoke.exceptions.Exit` for a `sys.exit` equivalent. (Or
  just call `sys.exit` if you want a no-questions-asked immediate exit that
  even our CLI machinery won't touch.)

The result::

    @task
    def test(c):
        result = c.local("./manage.py test my_app", warn=True)
        if not result and not confirm("Tests failed. Continue anyway?"):
            raise Exit("Aborting at user request.")

Other simple tasks
------------------

The next two tasks are simple one-liners, and you've already seen what replaced
the global ``local`` function::

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
difference is that we want to pass along our context object to preserve the
configuration context (such as loaded config files or CLI flags)::

    @task
    def prepare_deploy(c):
        test(c)
        commit(c)
        push(c)

Actual remote steps
-------------------

Note that up to this point, nothing truly Fabric-related has been in play -
`fabric.connection.Connection.local` is just a rebinding of `Context.run
<invoke.context.Context.run>`, Invoke's local subprocess execution method. Now
we get to the actual deploy step, which invokes
`fabric.connection.Connection.run` instead, executing remotely (on whichever
host the `fabric.connection.Connection` has been bound to).

``with cd`` is not fully implemented for the remote side of things, but we
expect it will be soon. For now we fall back to command chaining with ``&&``.
And, notably, now that we care about selecting host targets, we refer to our
earlier definition of a default host list -- ``my_hosts`` -- when declaring the
default host list for this task.

::

    @task(hosts=my_hosts)
    def deploy(c):
        code_dir = "/srv/django/myproject"
        if not c.run("test -d {}".format(code_dir), warn=True):
            cmd = "git clone user@vcshost:/path/to/repo/.git {}"
            c.run(cmd.format(code_dir))
        c.run("cd {} && git pull".format(code_dir))
        c.run("cd {} && touch app.wsgi".format(code_dir))

The whole thing
---------------

Now we have the entire, upgraded fabfile that will work with modern Fabric::

    from invoke import Exit
    from invocations.console import confirm

    from fabric import task

    my_hosts = ["my-server"]

    @task
    def test(c):
        result = c.local("./manage.py test my_app", warn=True)
        if not result and not confirm("Tests failed. Continue anyway?"):
            raise Exit("Aborting at user request.")

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

    @task(hosts=my_hosts)
    def deploy(c):
        code_dir = "/srv/django/myproject"
        if not c.run("test -d {}".format(code_dir), warn=True):
            cmd = "git clone user@vcshost:/path/to/repo/.git {}"
            c.run(cmd.format(code_dir))
        c.run("cd {} && git pull".format(code_dir))
        c.run("cd {} && touch app.wsgi".format(code_dir))
