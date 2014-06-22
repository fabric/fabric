=========
Changelog
=========

* :release:`1.9.0 <2014-06-08>`
* :feature:`1078` Add ``.command`` and ``.real_command`` attributes to
  ``local`` return value.  Thanks to Alexander Teves (``@alexanderteves``) and
  Konrad Hałas (``@konradhalas``).
* :feature:`938` Add an env var :ref:`env.effective_roles <effective_roles>`
  specifying roles used in the currently executing command. Thanks to
  Piotr Betkier for the patch.
* :feature:`1101` Reboot operation now supports custom command. Thanks to Jonas
  Lejon.
* :support:`1106` Fix a misleading/ambiguous example snippet in the ``fab``
  usage docs to be clearer. Thanks to ``@zed``.
* :release:`1.8.4 <2014-06-08>`
* :release:`1.7.4 <2014-06-08>`
* :bug:`898` Treat paths that begin with tilde "~" as absolute paths instead of
  relative. Thanks to Alex Plugaru for the patch and Dan Craig for the
  suggestion.
* :support:`1105 backported` Enhance ``setup.py`` to allow Paramiko 1.13+ under
  Python 2.6+. Thanks to to ``@Arfrever`` for catch & patch.
* :release:`1.8.3 <2014-03-21>`
* :release:`1.7.3 <2014-03-21>`
* :support:`- backported` Modified packaging data to reflect that Fabric
  requires Paramiko < 1.13 (which dropped Python 2.5 support.)
* :feature:`1082` Add ``pty`` passthrough kwarg to
  `~fabric.contrib.files.upload_template`.
* :release:`1.8.2 <2014-02-14>`
* :release:`1.7.2 <2014-02-14>`
* :bug:`955` Quote directories created as part of ``put``'s recursive directory
  uploads when ``use_sudo=True`` so directories with shell meta-characters
  (such as spaces) work correctly. Thanks to John Harris for the catch.
* :bug:`917` Correct an issue with ``put(use_sudo=True, mode=xxx)`` where the
  ``chmod`` was trying to apply to the wrong location. Thanks to Remco
  (``@nl5887``) for catch & patch.
* :bug:`1046` Fix typo preventing use of ProxyCommand in some situations.
  Thanks to Keith Yang.
* :release:`1.8.1 <2013-12-24>`
* :release:`1.7.1 <2013-12-24>`
* :release:`1.6.4 <2013-12-24>` 956, 957
* :release:`1.5.5 <2013-12-24>` 956, 957
* :bug:`956` Fix pty size detection when running inside Emacs. Thanks to
  `@akitada` for catch & patch.
* :bug:`957` Fix bug preventing use of :ref:`env.gateway <gateway>` with
  targets requiring password authentication. Thanks to Daniel González,
  `@Bengrunt` and `@adrianbn` for their bug reports.
* :feature:`741` Add :ref:`env.prompts <prompts>` dictionary, allowing
  users to set up custom prompt responses (similar to the built-in sudo prompt
  auto-responder.) Thanks to Nigel Owens and David Halter for the patch.
* :bug:`965 major` Tweak IO flushing behavior when in linewise (& thus
  parallel) mode so interwoven output is less frequent. Thanks to `@akidata`
  for catch & patch.
* :bug:`948` Handle connection failures due to server load and try connecting
  to hosts a number of times specified in :ref:`env.connection_attempts
  <connection-attempts>`.
* :release:`1.8.0 <2013-09-20>`
* :feature:`931` Allow overriding of `.abort` behavior via a custom
  exception-returning callable set as :ref:`env.abort_exception
  <abort-exception>`. Thanks to Chris Rose for the patch.
* :support:`984 backported` Make this changelog easier to read! Now with
  per-release sections, generated automatically from the old timeline source
  format.
* :feature:`910` Added a keyword argument to rsync_project to configure the
  default options. Thanks to ``@moorepants`` for the patch.
* :release:`1.7.0 <2013-07-26>`
* :release:`1.6.2 <2013-07-26>`
* :feature:`925` Added `contrib.files.is_link <.is_link>`. Thanks to `@jtangas`
  for the patch.
* :feature:`922` Task argument strings are now displayed when using
  :option:`fab -d <-d>`. Thanks to Kevin Qiu for the patch.
* :bug:`912` Leaving ``template_dir`` un-specified when using
  `.upload_template` in Jinja mode used to cause ``'NoneType' has no attribute
  'startswith'`` errors. This has been fixed. Thanks to Erick Yellott for catch
  & to Erick Yellott + Kevin Williams for patches.
* :feature:`924` Add new env var option :ref:`colorize-errors` to enable
  coloring errors and warnings. Thanks to Aaron Meurer for the patch.
* :bug:`593` Non-ASCII character sets in Jinja templates rendered within
  `.upload_template` would cause ``UnicodeDecodeError`` when uploaded. This has
  been addressed by encoding as ``utf-8`` prior to upload. Thanks to Sébastien
  Fievet for the catch.
* :feature:`908` Support loading SSH keys from memory. Thanks to Caleb Groom
  for the patch.
* :bug:`171` Added missing cross-references from ``env`` variables documentation
  to corresponding command-line options. Thanks to Daniel D. Beck for the
  contribution.
* :bug:`884` The password cache feature was not working correctly with
  password-requiring SSH gateway connections. That's fixed now. Thanks to Marco
  Nenciarini for the catch.
* :feature:`826` Enable sudo extraction of compressed archive via `use_sudo`
  kwarg in `.upload_project`. Thanks to ``@abec`` for the patch.
* :bug:`694 major` Allow users to work around ownership issues in the default
  remote login directory: add ``temp_dir`` kwarg for explicit specification of
  which "bounce" folder to use when calling `.put` with ``use_sudo=True``.
  Thanks to Devin Bayer for the report & Dieter Plaetinck / Jesse Myers for
  suggesting the workaround.
* :bug:`882` Fix a `.get` bug regarding spaces in remote working directory
  names. Thanks to Chris Rose for catch & patch.
* :release:`1.6.1 <2013-05-23>`
* :bug:`868` Substantial speedup of parallel tasks by removing an unnecessary
  blocking timeout in the ``JobQueue`` loop. Thanks to Simo Kinnunen for the
  patch.
* :bug:`328` `.lcd` was no longer being correctly applied to
  `.upload_template`; this has been fixed. Thanks to Joseph Lawson for the
  catch.
* :feature:`812` Add ``use_glob`` option to `.put` so users trying to upload
  real filenames containing glob patterns (``*``, ``[`` etc) can disable the
  default globbing behavior. Thanks to Michael McHugh for the patch.
* :bug:`864 major` Allow users to disable Fabric's auto-escaping in
  `.run`/`.sudo`.  Thanks to Christian Long and Michael McHugh for the patch.
* :bug:`870` Changes to shell env var escaping highlighted some extraneous and
  now damaging whitespace in `with path(): <.path>`. This has been removed and
  a regression test added.
* :bug:`871` Use of string mode values in `put(local, remote, mode="NNNN")
  <.put>` would sometimes cause ``Unsupported operand`` errors. This has been
  fixed.
* :bug:`84 major` Fixed problem with missing -r flag in Mac OS X sed version.
  Thanks to Konrad Hałas for the patch.
* :bug:`861` Gracefully handle situations where users give a single string
  literal to ``env.hosts``. Thanks to Bill Tucker for catch & patch.
* :bug:`367` Expand paths with tilde inside (``contrib.files``). Thanks to
  Konrad Hałas for catch & patch.
* :feature:`845 backported` Downstream synchronization option implemented for
  `~fabric.contrib.project.rsync_project`. Thanks to Antonio Barrero for the
  patch.
* :release:`1.6.0 <2013-03-01>`
* :release:`1.5.4 <2013-03-01>`
* :bug:`844` Account for SSH config overhaul in Paramiko 1.10 by e.g. updating
  treatment of ``IdentityFile`` to handle multiple values. **This and related
  SSH config parsing changes are backwards incompatible**; we are including
  them in this release because they do fix incorrect, off-spec behavior.
* :bug:`843` Ensure string ``pool_size`` values get run through ``int()``
  before deriving final result (stdlib ``min()`` has odd behavior here...).
  Thanks to Chris Kastorff for the catch.
* :bug:`839` Fix bug in `~fabric.contrib.project.rsync_project` where IPv6
  address were not always correctly detected. Thanks to Antonio Barrero for
  catch & patch.
* :bug:`587` Warn instead of aborting when :ref:`env.use_ssh_config
  <use-ssh-config>` is True but the configured SSH conf file doesn't exist.
  This allows multi-user fabfiles to enable SSH config without causing hard
  stops for users lacking SSH configs. Thanks to Rodrigo Pimentel for the
  report.
* :feature:`821` Add `~fabric.context_managers.remote_tunnel` to allow reverse
  SSH tunneling (exposing locally-visible network ports to the remote end).
  Thanks to Giovanni Bajo for the patch.
* :feature:`823` Add :ref:`env.remote_interrupt <remote-interrupt>` which
  controls whether Ctrl-C is forwarded to the remote end or is captured locally
  (previously, only the latter behavior was implemented). Thanks to Geert
  Jansen for the patch.
* :release:`1.5.3 <2013-01-28>`
* :bug:`806` Force strings given to ``getpass`` during password prompts to be
  ASCII, to prevent issues on some platforms when Unicode is encountered.
  Thanks to Alex Louden for the patch.
* :bug:`805` Update `~fabric.context_managers.shell_env` to play nice with
  Windows (7, at least) systems and `~fabric.operations.local`. Thanks to
  Fernando Macedo for the patch.
* :bug:`654` Parallel runs whose sum total of returned data was large (e.g.
  large return values from the task, or simply a large number of hosts in the
  host list) were causing frustrating hangs. This has been fixed.
* :feature:`402` Attempt to detect stale SSH sessions and reconnect when they
  arise. Thanks to `@webengineer` for the patch.
* :bug:`791` Cast `~fabric.operations.reboot`'s ``wait`` parameter to a numeric
  type in case the caller submitted a string by mistake. Thanks to Thomas
  Schreiber for the patch.
* :bug:`703 major` Add a ``shell`` kwarg to many methods in
  `~fabric.contrib.files` to help avoid conflicts with
  `~fabric.context_managers.cd` and similar.  Thanks to `@mikek` for the patch.
* :feature:`730` Add :ref:`env.system_known_hosts/--system-known-hosts
  <system-known-hosts>` to allow loading a user-specified system-level SSH
  ``known_hosts`` file. Thanks to Roy Smith for the patch.
* :release:`1.5.2 <2013-01-15>`
* :feature:`818` Added :ref:`env.eagerly_disconnect <eagerly-disconnect>`
  option to help prevent pile-up of many open connections.
* :feature:`706` Added :ref:`env.tasks <env-tasks>`, returning list of tasks to
  be executed by current ``fab`` command.
* :bug:`766` Use the variable name of a new-style ``fabric.tasks.Task``
  subclass object when the object name attribute is undefined.  Thanks to
  `@todddeluca` for the patch.
* :bug:`604` Fixed wrong treatment of backslashes in put operation when uploading
  directory tree on Windows. Thanks to Jason Coombs for the catch and
  `@diresys` & Oliver Janik for the patch.
  for the patch.
* :bug:`792` The newish `~fabric.context_managers.shell_env` context manager
  was incorrectly omitted from the ``fabric.api`` import endpoint. This has
  been remedied. Thanks to Vishal Rana for the catch.
* :feature:`735` Add ``ok_ret_codes`` option to ``env`` to allow alternate
  return codes to be treated os "ok". Thanks to Andy Kraut for the pull request.
* :bug:`775` Shell escaping was incorrectly applied to the value of ``$PATH``
  updates in our shell environment handling, causing (at the very least)
  `~fabric.operations.local` binary paths to become inoperable in certain
  situations.  This has been fixed.
* :feature:`787` Utilize new Paramiko feature allowing us to skip the use of
  temporary local files when using file-like objects in
  `~fabric.operations.get`/`~fabric.operations.put`.
* :feature:`249` Allow specification of remote command timeout value by
  setting :ref:`env.command_timeout <command-timeout>`. Thanks to Paul
  McMillan for suggestion & initial patch.
* Added current host string to prompt abort error messages.
* :release:`1.5.1 <2012-11-15>`
* :bug:`776` Fixed serious-but-non-obvious bug in direct-tcpip driven
  gatewaying (e.g. that triggered by ``-g`` or ``env.gateway``.) Should work
  correctly now.
* :bug:`771` Sphinx autodoc helper `~fabric.docs.unwrap_tasks` didn't play nice
  with ``@task(name=xxx)`` in some situations. This has been fixed.
* :release:`1.5.0 <2012-11-06>`
* :release:`1.4.4 <2012-11-06>`
* :feature:`38` (also :issue:`698`) Implement both SSH-level and
  ``ProxyCommand``-based gatewaying for SSH traffic. (This is distinct from
  tunneling non-SSH traffic over the SSH connection, which is :issue:`78` and
  not implemented yet.)

    * Thanks in no particular order to Erwin Bolwidt, Oskari Saarenmaa, Steven
      Noonan, Vladimir Lazarenko, Lincoln de Sousa, Valentino Volonghi, Olle
      Lundberg and Github user `@acrish` for providing the original patches to
      both Fabric and Paramiko.

* :feature:`684 backported` (also :issue:`569`) Update how
  `~fabric.decorators.task` wraps task functions to preserve additional
  metadata; this allows decorated functions to play nice with Sphinx autodoc.
  Thanks to Jaka Hudoklin for catch & patch.
* :support:`103` (via :issue:`748`) Long standing Sphinx autodoc issue requiring
  error-prone duplication of function signatures in our API docs has been
  fixed. Thanks to Alex Morega for the patch.
* :bug:`767 major` Fix (and add test for) regression re: having linewise output
  automatically activate when parallelism is in effect. Thanks to Alexander
  Fortin and Dustin McQuay for the bug reports.
* :bug:`736 major` Ensure context managers that build env vars play nice with
  ``contextlib.nested`` by deferring env var reference to entry time, not call
  time. Thanks to Matthew Tretter for catch & patch.
* :feature:`763` Add :option:`--initial-password-prompt <-I>` to allow
  prefilling the password cache at the start of a run. Great for sudo-powered
  parallel runs.
* :feature:`665` (and #629) Update `~fabric.contrib.files.upload_template` to
  have a more useful return value, namely that of its internal
  `~fabric.operations.put` call. Thanks to Miquel Torres for the catch &
  Rodrigue Alcazar for the patch.
* :feature:`578` Add ``name`` argument to `~fabric.decorators.task` (:ref:`docs
  <task-decorator-arguments>`) to allow overriding of the default "function
  name is task name" behavior. Thanks to Daniel Simmons for catch & patch.
* :feature:`761` Allow advanced users to parameterize ``fabric.main.main()`` to
  force loading of specific fabfiles.
* :bug:`749` Gracefully work around calls to ``fabric.version`` on systems
  lacking ``/bin/sh`` (which causes an ``OSError`` in ``subprocess.Popen``
  calls.)
* :feature:`723` Add the ``group=`` argument to
  `~fabric.operations.sudo`. Thanks to Antti Kaihola for the pull request.
* :feature:`725` Updated `~fabric.operations.local` to allow override
  of which local shell is used. Thanks to Mustafa Khattab.
* :bug:`704 major` Fix up a bunch of Python 2.x style ``print`` statements to
  be forwards compatible. Thanks to Francesco Del Degan for the patch.
* :feature:`491` (also :feature:`385`) IPv6 host string support. Thanks to Max
  Arnold for the patch.
* :feature:`699` Allow `name` attribute on file-like objects for get/put. Thanks
  to Peter Lyons for the pull request.
* :bug:`711 major` `~fabric.sftp.get` would fail when filenames had % in their
  path.  Thanks to John Begeman
* :bug:`702 major` `~fabric.operations.require` failed to test for "empty"
  values in the env keys it checks (e.g.
  ``require('a-key-whose-value-is-an-empty-list')`` would register a successful
  result instead of alerting that the value was in fact empty. This has been
  fixed, thanks to Rich Schumacher.
* :bug:`718` ``isinstance(foo, Bar)`` is used in `~fabric.main` instead
  of ``type(foo) == Bar`` in order to fix some edge cases.
  Thanks to Mikhail Korobov.
* :bug:`693` Fixed edge case where ``abort`` driven failures within parallel
  tasks could result in a top level exception (a ``KeyError``) regarding error
  handling. Thanks to Marcin Kuźmiński for the report.
* :support:`681 backported` Fixed outdated docstring for
  `~fabric.decorators.runs_once` which claimed it would get run multiple times
  in parallel mode. That behavior was fixed in an earlier release but the docs
  were not updated. Thanks to Jan Brauer for the catch.
* :release:`1.4.3 <2012-07-06>`
* :release:`1.3.8 <2012-07-06>`
* :feature:`263` Shell environment variable support for
  `~fabric.operations.run`/`~fabric.operations.sudo` added in the form of the
  `~fabric.context_managers.shell_env` context manager. Thanks to Oliver
  Tonnhofer for the original pull request, and to Kamil Kisiel for the final
  implementation.
* :feature:`669` Updates to our Windows compatibility to rely more heavily on
  cross-platform Python stdlib implementations. Thanks to Alexey Diyan for the
  patch.
* :bug:`671` :ref:`reject-unknown-hosts` sometimes resulted in a password
  prompt instead of an abort. This has been fixed. Thanks to Roy Smith for the
  report.
* :bug:`659` Update docs to reflect that `~fabric.operations.local` currently
  honors :ref:`env.path <env-path>`. Thanks to `@floledermann
  <https://github.com/floledermann>`_ for the catch.
* :bug:`652` Show available commands when aborting on invalid command names.
* :support:`651 backported` Added note about nesting ``with`` statements on
  Python 2.6+.  Thanks to Jens Rantil for the patch.
* :bug:`649` Don't swallow non-``abort``-driven exceptions in parallel mode.
  Fabric correctly printed such exceptions, and returned them from
  `~fabric.tasks.execute`, but did not actually cause the child or parent
  processes to halt with a nonzero status. This has been fixed.
  `~fabric.tasks.execute` now also honors :ref:`env.warn_only <warn_only>` so
  users may still opt to call it by hand and inspect the returned exceptions,
  instead of encountering a hard stop. Thanks to Matt Robenolt for the catch.
* :feature:`241` Add the command executed as a ``.command`` attribute to the
  return value of `~fabric.operations.run`/`~fabric.operations.sudo`. (Also
  includes a second attribute containing the "real" command executed, including
  the shell wrapper and any escaping.)
* :feature:`646` Allow specification of which local streams to use when
  `~fabric.operations.run`/`~fabric.operations.sudo` print the remote
  stdout/stderr, via e.g. ``run("command", stderr=sys.stdout)``.
* :support:`645 backported` Update Sphinx docs to work well when run out of a
  source tarball as opposed to a Git checkout. Thanks again to `@Arfrever` for
  the catch.
* :support:`640 backported` (also :issue:`644`) Update packaging manifest so
  sdist tarballs include all necessary test & doc files. Thanks to Mike Gilbert
  and `@Arfrever` for catch & patch.
* :feature:`627` Added convenient ``quiet`` and ``warn_only`` keyword arguments
  to `~fabric.operations.run`/`~fabric.operations.sudo` which are aliases for
  ``settings(hide('everything'), warn_only=True)`` and
  ``settings(warn_only=True)``, respectively. (Also added corresponding
  `context <fabric.context_managers.quiet>` `managers
  <fabric.context_managers.warn_only>`.) Useful for remote program calls which
  are expected to fail and/or whose output doesn't need to be shown to users.
* :feature:`633` Allow users to turn off host list deduping by setting
  :ref:`env.dedupe_hosts <dedupe_hosts>` to ``False``. This enables running the
  same task multiple times on a single host, which was previously not possible.
* :support:`634 backported` Clarified that `~fabric.context_managers.lcd` does
  no special handling re: the user's current working directory, and thus
  relative paths given to it will be relative to ``os.getcwd()``. Thanks to
  `@techtonik <https://github.com/techtonik>`_ for the catch.
* :release:`1.4.2 <2012-05-07>`
* :release:`1.3.7 <2012-05-07>`
* :bug:`562` Agent forwarding would error out or freeze when multiple uses of
  the forwarded agent were used per remote invocation (e.g. a single
  `~fabric.operations.run` command resulting in multiple Git or SVN checkouts.)
  This has been fixed thanks to Steven McDonald and GitHub user `@lynxis`.
* :support:`626 backported` Clarity updates to the tutorial. Thanks to GitHub
  user `m4z` for the patches.
* :bug:`625` `~fabric.context_managers.hide`/`~fabric.context_managers.show`
  did not correctly restore prior display settings if an exception was raised
  inside the block. This has been fixed.
* :bug:`624` Login password prompts did not always display the username being
  authenticated for. This has been fixed. Thanks to Nick Zalutskiy for catch &
  patch.
* :bug:`617` Fix the ``clean_revert`` behavior of
  `~fabric.context_managers.settings` so it doesn't ``KeyError`` for newly
  created settings keys. Thanks to Chris Streeter for the catch.
* :feature:`615` Updated `~fabric.operations.sudo` to honor the new setting
  :ref:`env.sudo_user <sudo_user>` as a default for its ``user`` kwarg.
* :bug:`616` Add port number to the error message displayed upon connection
  failures.
* :bug:`609` (and :issue:`564`) Document and clean up :ref:`env.sudo_prefix
  <sudo_prefix>` so it can be more easily modified by users facing uncommon
  use cases. Thanks to GitHub users `3point2` for the cleanup and `SirScott`
  for the documentation catch.
* :bug:`610` Change detection of ``env.key_filename``'s type (added as part of
  SSH config support in 1.4) so it supports arbitrary iterables. Thanks to
  Brandon Rhodes for the catch.
* :release:`1.4.1 <2012-04-04>`
* :release:`1.3.6 <2012-04-04>`
* :bug:`608` Add ``capture`` kwarg to `~fabric.contrib.project.rsync_project`
  to aid in debugging rsync problems.
* :bug:`607` Allow `~fabric.operations.local` to display stdout/stderr when it
  warns/aborts, if it was capturing them.
* :bug:`395` Added :ref:`an FAQ entry <init-scripts-pty>` detailing how to
  handle init scripts which misbehave when a pseudo-tty is allocated.
* :bug:`568` `~fabric.tasks.execute` allowed too much of its internal state
  changes (to variables such as ``env.host_string`` and ``env.parallel``) to
  persist after execution completed; this caused a number of different
  incorrect behaviors. `~fabric.tasks.execute` has been overhauled to clean up
  its own state changes -- while preserving any state changes made by the task
  being executed.
* :bug:`584` `~fabric.contrib.project.upload_project` did not take explicit
  remote directory location into account when untarring, and now uses
  `~fabric.context_managers.cd` to address this. Thanks to Ben Burry for the
  patch.
* :bug:`458` `~fabric.decorators.with_settings` did not perfectly match
  `~fabric.context_managers.settings`, re: ability to inline additional context
  managers. This has been corrected. Thanks to Rory Geoghegan for the patch.
* :bug:`499` `contrib.files.first <fabric.contrib.files.first>` used an
  outdated function signature in its wrapped `~fabric.contrib.files.exists`
  call. This has been fixed. Thanks to Massimiliano Torromeo for catch & patch.
* :bug:`551` :option:`--list <-l>` output now detects terminal window size
  and truncates (or doesn't truncate) accordingly. Thanks to Horacio G. de Oro
  for the initial pull request.
* :bug:`572` Parallel task aborts (as oppposed to unhandled exceptions) now
  correctly print their abort messages instead of tracebacks, and cause the
  parent process to exit with the correct (nonzero) return code. Thanks to Ian
  Langworth for the catch.
* :bug:`306` Remote paths now use posixpath for a separator. Thanks to Jason
  Coombs for the patch.
* :release:`1.4.0 <2012-02-13>`
* :release:`1.3.5 <2012-02-13>`
* :release:`1.2.6 <2012-02-13>`
* :release:`1.1.8 <2012-02-13>`
* :bug:`495` Fixed documentation example showing how to subclass
  `~fabric.tasks.Task`. Thanks to Brett Haydon for the catch and Mark Merritt
  for the patch.
* :bug:`410` Fixed a bug where using the `~fabric.decorators.task` decorator
  inside/under another decorator such as `~fabric.decorators.hosts` could cause
  that task to become invalid when invoked by name (due to how old-style vs
  new-style tasks are detected.) Thanks to Dan Colish for the initial patch.
* :feature:`559` `~fabric.contrib.project.rsync_project` now allows users to
  append extra SSH-specific arguments to ``rsync``'s ``--rsh`` flag.
* :feature:`138` :ref:`env.port <port>` may now be written to at fabfile module
  level to set a default nonstandard port number. Previously this value was
  read-only.
* :feature:`3` Fabric can now load a subset of SSH config functionality
  directly from your local ``~/.ssh/config`` if :ref:`env.use_ssh_config
  <use-ssh-config>` is set to ``True``. See :ref:`ssh-config` for details.
  Thanks to Kirill Pinchuk for the initial patch.
* :feature:`12` Added the ability to try connecting multiple times to
  temporarily-down remote systems, instead of immediately failing. (Default
  behavior is still to only try once.) See :ref:`env.timeout <timeout>` and
  :ref:`env.connection_attempts <connection-attempts>` for controlling both
  connection timeouts and total number of attempts. `~fabric.operations.reboot`
  has also been overhauled (but practically deprecated -- see its updated
  docs.)
* :feature:`474` `~fabric.tasks.execute` now allows you to access the executed
  task's return values, by itself returning a dictionary whose keys are the
  host strings executed against.
* :bug:`487 major` Overhauled the regular expression escaping performed in
  `~fabric.contrib.files.append` and `~fabric.contrib.files.contains` to try
  and handle more corner cases. Thanks to Neilen Marais for the patch.
* :support:`532` Reorganized and cleaned up the output of ``fab --help``.
* :feature:`8` Added :option:`--skip-bad-hosts`/:ref:`env.skip_bad_hosts
  <skip-bad-hosts>` option to allow skipping past temporarily down/unreachable
  hosts.
* :feature:`13` Env vars may now be set at runtime via the new :option:`--set`
  command-line flag.
* :feature:`506` A new :ref:`output alias <output-aliases>`, ``commands``, has
  been added, which allows hiding remote stdout and local "running command X"
  output lines.
* :feature:`72` SSH agent forwarding support has made it into Fabric's SSH
  library, and hooks for using it have been added (disabled by default; use
  :option:`-A` or :ref:`env.forward_agent <forward-agent>` to enable.) Thanks
  to Ben Davis for porting an existing Paramiko patch to `ssh` and providing
  the necessary tweak to Fabric.
* :release:`1.3.4 <2012-01-12>`
* :bug:`492` `@parallel <fabric.decorators.parallel>` did not automatically
  trigger :ref:`linewise output <linewise-output>`, as was intended. This has
  been fixed. Thanks to Brandon Huey for the catch.
* :bug:`510` Parallel mode is incompatible with user input, such as
  password/hostname prompts, and was causing cryptic `Operation not supported
  by device` errors when such prompts needed to be displayed. This behavior has
  been updated to cleanly and obviously ``abort`` instead.
* :bug:`494` Fixed regression bug affecting some `env` values such as
  `env.port` under parallel mode. Symptoms included
  `~fabric.contrib.project.rsync_project` bailing out due to a None port value
  when run under `@parallel <fabric.decorators.parallel>`. Thanks to Rob
  Terhaar for the report.
* :bug:`339` Don't show imported `~fabric.colors` members in :option:`--list
  <-l>` output.  Thanks to Nick Trew for the report.
* :release:`1.3.3 <2011-11-23>`
* :release:`1.2.5 <2011-11-23>`
* :release:`1.1.7 <2011-11-23>`
* :bug:`441` Specifying a task module as a task on the command line no longer
  blows up but presents the usual "no task by that name" error message instead.
  Thanks to Mitchell Hashimoto for the catch.
* :bug:`475` Allow escaping of equals signs in per-task args/kwargs.
* :bug:`450` Improve traceback display when handling ``ImportError`` for
  dependencies. Thanks to David Wolever for the patches.
* :bug:`446` Add QNX to list of secondary-case `~fabric.contrib.files.sed`
  targets. Thanks to Rodrigo Madruga for the tip.
* :bug:`443` `~fabric.contrib.files.exists` didn't expand tildes; now it does.
  Thanks to Riccardo Magliocchetti for the patch.
* :bug:`437` `~fabric.decorators.with_settings` now correctly preserves the
  wrapped function's docstring and other attributes. Thanks to Eric Buckley for
  the catch and Luke Plant for the patch.
* :bug:`400` Handle corner case of systems where ``pwd.getpwuid`` raises
  ``KeyError`` for the user's UID instead of returning a valid string. Thanks
  to Dougal Matthews for the catch.
* :bug:`397` Some poorly behaved objects in third party modules triggered
  exceptions during Fabric's "classic or new-style task?" test. A fix has been
  added which tries to work around these.
* :bug:`341` `~fabric.contrib.files.append` incorrectly failed to detect that
  the line(s) given already existed in files hidden to the remote user, and
  continued appending every time it ran. This has been fixed. Thanks to
  Dominique Peretti for the catch and Martin Vilcans for the patch.
* :bug:`342` Combining `~fabric.context_managers.cd` with
  `~fabric.operations.put` and its ``use_sudo`` keyword caused an unrecoverable
  error. This has been fixed. Thanks to Egor M for the report.
* :bug:`482` Parallel mode should imply linewise output; omission of this
  behavior was an oversight.
* :bug:`230` Fix regression re: combo of no fabfile & arbitrary command use.
  Thanks to Ali Saifee for the catch.
* :release:`1.3.2 <2011-11-07>`
* :release:`1.2.4 <2011-11-07>`
* :release:`1.1.6 <2011-11-07>`
* :support:`459 backported` Update our `setup.py` files to note that PyCrypto
  released 2.4.1, which fixes the setuptools problems.
* :support:`467 backported` (also :issue:`468`, :issue:`469`) Handful of
  documentation clarification tweaks. Thanks to Paul Hoffman for the patches.
* :release:`1.3.1 <2011-10-24>`
* :bug:`457` Ensured that Fabric fast-fails parallel tasks if any child
  processes encountered errors. Previously, multi-task invocations would
  continue to the 2nd, etc task when failures occurred, which does not fit with
  how Fabric usually behaves. Thanks to Github user ``sdcooke`` for the report
  and Morgan Goose for the fix.
* :release:`1.3.0 <2011-10-23>`
* :release:`1.2.3 <2011-10-23>`
* :release:`1.1.5 <2011-10-23>`
* :release:`1.0.5 <2011-10-23>`
* :support:`275` To support an edge use case of the features released in
  :issue:`19`, and to lay the foundation for :issue:`275`, we have forked
  Paramiko into the `Python 'ssh' library <http://pypi.python.org/pypi/ssh/>`_
  and changed our dependency to it for Fabric 1.3 and higher. This may have
  implications for the more uncommon install use cases, and package
  maintainers, but we hope to iron out any issues as they come up.
* :bug:`323` `~fabric.operations.put` forgot how to expand leading tildes in
  the remote file path. This has been corrected. Thanks to Piet Delport for the
  catch.
* :feature:`21` It is now possible, using the new `~fabric.tasks.execute` API
  call, to execute task objects (by reference or by name) from within other
  tasks or in library mode. `~fabric.tasks.execute` honors the other tasks'
  `~fabric.decorators.hosts`/`~fabric.decorators.roles` decorators, and also
  supports passing in explicit host and/or role arguments.
* :feature:`19` Tasks may now be optionally executed in parallel. Please see
  the :ref:`parallel execution docs <parallel-execution>` for details. Major
  thanks to Morgan Goose for the initial implementation.
* :bug:`182` During display of remote stdout/stderr, Fabric occasionally
  printed extraneous line prefixes (which in turn sometimes overwrote wrapped
  text.) This has been fixed.
* :bug:`430` Tasks decorated with `~fabric.decorators.runs_once` printed
  extraneous 'Executing...' status lines on subsequent invocations. This is
  noisy at best and misleading at worst, and has been corrected. Thanks to
  Jacob Kaplan-Moss for the report.
* :release:`1.2.2 <2011-09-01>`
* :release:`1.1.4 <2011-09-01>`
* :release:`1.0.4 <2011-09-01>`
* :bug:`252` `~fabric.context_managers.settings` would silently fail to set
  ``env`` values for keys which did not exist outside the context manager
  block.  It now works as expected. Thanks to Will Maier for the catch and
  suggested solution.
* :support:`393 backported` Fixed a typo in an example code snippet in the task
  docs.  Thanks to Hugo Garza for the catch.
* :bug:`396` :option:`--shortlist` broke after the addition of
  :option:`--list-format <-F>` and no longer displayed the short list format
  correctly. This has been fixed.
* :bug:`373` Re-added missing functionality preventing :ref:`host exclusion
  <excluding-hosts>` from working correctly.
* :bug:`303` Updated terminal size detection to correctly skip over non-tty
  stdout, such as when running ``fab taskname | other_command``.
* :release:`1.2.1 <2011-08-21>`
* :release:`1.1.3 <2011-08-21>`
* :release:`1.0.3 <2011-08-21>`
* :bug:`417` :ref:`abort-on-prompts` would incorrectly abort when set to True,
  even if both password and host were defined. This has been fixed. Thanks to
  Valerie Ishida for the report.
* :support:`416 backported` Updated documentation to reflect move from Redmine
  to Github.
* :bug:`389` Fixed/improved error handling when Paramiko import fails. Thanks
  to Brian Luft for the catch.
* :release:`1.2.0 <2011-07-12>`
* :feature:`22` Enhanced `@task <fabric.decorators.task>` to add :ref:`aliasing
  <task-aliases>`, :ref:`per-module default tasks <default-tasks>`, and
  :ref:`control over the wrapping task class <task-decorator-and-classes>`.
  Thanks to Travis Swicegood for the initial work and collaboration.
* :bug:`380` Improved unicode support when testing objects for being
  string-like. Thanks to Jiri Barton for catch & patch.
* :support:`382` Experimental overhaul of changelog formatting & process to
  make supporting multiple lines of development less of a hassle.
* :release:`1.1.2 <2011-07-07>`
* :release:`1.0.2 <2011-06-24>`
