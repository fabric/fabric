:orphan:

=========
Changelog
=========

How to read
===========

This changelog lists each bugfix, feature addition, etc in the order they were
checked into Fapric's source code repository. Published releases are bolded,
dated and inserted at the appropriate points in the timeline.

To find out the changes included in a given release, simply look at the entries
between that release and the previous one from the same release line (e.g.
1.1.4 down through 1.1.3 would be the effective changelog for the 1.1.4
release.)

Bugfixes to older release lines are always forward-ported to newer releases,
and this is reflected in the changelog. Thus, the changelog for e.g. 1.2.2
might contain entries for the 1.1 and 1.0 lines as well, because those changes
would have also been included in the 1.2 line.


Changelog
=========

* :bug:`430` Tasks decorated with `~fapric.decorators.runs_once` printed
  extraneous 'Executing...' status lines on subsequent invocations. This is
  noisy at best and misleading at worst, and has been corrected. Thanks to
  Jacob Kaplan-Moss for the report.
* :release:`1.2.2 <2011-09-01>`
* :release:`1.1.4 <2011-09-01>`
* :release:`1.0.4 <2011-09-01>`
* :bug:`252` `~fapric.context_managers.settings` would silently fail to set
  ``env`` values for keys which did not exist outside the context manager
  block.  It now works as expected. Thanks to Will Maier for the catch and
  suggested solution.
* :support:`393` Fixed a typo in an example code snippet in the task docs.
  Thanks to Hugo Garza for the catch.
* :bug:`396` :option:`--shortlist` broke after the addition of
  :option:`--list-format <-F>` and no longer displayed the short list format
  correctly. This has been fixed.
* :bug:`373` Re-added missing functionality preventing :ref:`host exclusion
  <excluding-hosts>` from working correctly.
* :bug:`303` Updated terminal size detection to correctly skip over non-tty
  stdout, such as when running ``fap taskname | other_command``.
* :release:`1.2.1 <2011-08-21>`
* :release:`1.1.3 <2011-08-21>`
* :release:`1.0.3 <2011-08-21>`
* :bug:`417` :ref:`abort-on-prompts` would incorrectly abort when set to True,
  even if both password and host were defined. This has been fixed. Thanks to
  Valerie Ishida for the report.
* :support:`416` Updated documentation to reflect move from Redmine to Github.
* :bug:`389` Fixed/improved error handling when Paramiko import fails. Thanks
  to Brian Luft for the catch.
* :release:`1.2.0 <2011-07-12>`
* :feature:`22` Enhanced `@task <fapric.decorators.task>` to add :ref:`aliasing
  <task-aliases>`, :ref:`per-module default tasks <default-tasks>`, and
  :ref:`control over the wrapping task class <task-decorator-and-classes>`.
  Thanks to Travis Swicegood for the initial work and collaboration.
* :bug:`380` Improved unicode support when testing objects for being
  string-like. Thanks to Jiri Barton for catch & patch.
* :support:`382` Experimental overhaul of changelog formatting & process to
  make supporting multiple lines of development less of a hassle.
* :release:`1.1.2 <2011-07-07>` (see below for details)
* :release:`1.0.2 <2011-06-24>` (see below for details)


Prehistory
==========

The content below this section comes from older versions of Fapric which wrote
out changelogs to individual, undated files. They have been concatenated and
preserved here for historical reasons, and may not be in strict chronological
order.

----


Changes in version 1.1.2 (2011-07-07)
=====================================

Bugfixes
--------

* :issue:`375`: The logic used to separate tasks from modules when running
  ``fap --list`` incorrectly considered task classes implementing the mapping
  interface to be modules, not individual tasks. This has been corrected.
  Thanks to Vladimir Mihailenco for the catch.


Changes in version 1.1.1 (2011-06-29)
=====================================

Bugfixes
--------

* The public API for `~fapric.tasks.Task` mentioned use of the ``run()``
  method, but Fapric's main execution loop had not been updated to look for and
  call it, forcing users who subclassed `~fapric.tasks.Task` to define
  ``__call__()`` instead. This was an oversight and has been corrected.

  .. seealso:: :ref:`task-subclasses`


Changes in version 1.1 (2011-06-24)
===================================

This page lists all changes made to Fapric in its 1.1.0 release.

.. note::
    This release also includes all applicable changes from the 1.0.2 release.

Highlights
----------

* :issue:`76`: :ref:`New-style tasks <new-style-tasks>` have been added. With
  the addition of the `~fapric.decorators.task` decorator and the
  `~fapric.tasks.Task` class, you can now "opt-in" and explicitly mark task
  functions as tasks, and Fapric will ignore the rest. The original behavior
  (now referred to as :ref:`"classic" tasks <classic-tasks>`) will still take
  effect if no new-style tasks are found. Major thanks to Travis Swicegood for
  the original implementation.
* :issue:`56`: Namespacing is now possible: Fapric will crawl imported module
  objects looking for new-style task objects and build a dotted hierarchy
  (tasks named e.g. ``web.deploy`` or ``db.migrations.run``), allowing for
  greater organization. See :ref:`namespaces` for details. Thanks again to
  Travis Swicegood.


Feature additions
-----------------

* :issue:`10`: `~fapric.contrib.upload_project` now allows control over the
  local and remote directory paths, and has improved error handling. Thanks to
  Rodrigue Alcazar for the patch.
* As part of :issue:`56` (highlighted above), added :option:`--list-format
  <-F>` to allow specification of a nested output format from :option:`--list
  <-l>`.
* :issue:`107`: `~fapric.operations.require`'s ``provided_by`` kwarg now
  accepts iterables in addition to single values. Thanks to Thomas Ballinger
  for the patch.
* :issue:`117`: `~fapric.contrib.files.upload_template` now supports the
  `~fapric.operations.put` flags ``mirror_local_mode`` and ``mode``. Thanks to
  Joe Stump for the suggestion and Thomas Ballinger for the patch.
* :issue:`154`: `~fapric.contrib.files.sed` now allows customized regex flags
  to be specified via a new ``flags`` parameter. Thanks to Nick Trew for the
  suggestion and Morgan Goose for initial implementation.
* :issue:`170`: Allow :ref:`exclusion <excluding-hosts>` of specific hosts from
  the final run list. Thanks to Casey Banner for the suggestion and patch.
* :issue:`189`: Added :option:`--abort-on-prompts`/:ref:`env.abort_on_prompts
  <abort-on-prompts>` to allow a more non-interactive behavior,
  aborting/exiting instead of trying to prompt the running user. Thanks to
  Jeremy Avnet and Matt Chisholm for the initial patch.
* :issue:`273`: `~fapric.contrib.files.upload_template` now offers control over
  whether it attempts to create backups of pre-existing destination files.
  Thanks to Ales Zoulek for the suggestion and initial patch.
* :issue:`283`: Added the `~fapric.decorators.with_settings` decorator to allow
  application of env var settings to an entire function, as an alternative to
  using the `~fapric.context_managers.settings` context manager. Thanks to
  Travis Swicegood for the patch.
* :issue:`353`: Added :option:`--keepalive`/:ref:`env.keepalive <keepalive>` to
  allow specification of an SSH keepalive parameter for troublesome network
  connections. Thanks to Mark Merritt for catch & patch.

Bugfixes
--------

* :issue:`115`: An implementation detail causing host lists to lose order
  when deduped by the ``fap`` execution loop, has been patched to preserve
  order instead. So e.g. ``fap -H a,b,c`` (or setting ``env.hosts = ['a', 'b',
  'c']``) will now always run on ``a``, then ``b``, then ``c``. Previously,
  there was a chance the order could get mixed up during deduplication. Thanks
  to Rohit Aggarwal for the report.
* :issue:`345`: `~fapric.contrib.files.contains` returned the stdout of its
  internal ``grep`` command instead of success/failure, causing incorrect
  behavior when stderr exists and is combined with stdout. This has been
  corrected. Thanks to Szymon Reichmann for catch and patch.

Documentation updates
---------------------

* Documentation for task declaration has been moved from
  :doc:`/usage/execution` into its own docs page, :doc:`/usage/tasks`, as a
  result of the changes added in :issue:`76` and :issue:`56`.
* :issue:`184`: Make the usage of `~fapric.contrib.project.rsync_project`'s
  ``local_dir`` argument more obvious, regarding its use in the ``rsync`` call.
  (Specifically, so users know they can pass in multiple, space-joined
  directory names instead of just one single directory.)

Internals
---------

* :issue:`307`: A whole pile of minor PEP8 tweaks. Thanks to Markus Gattol for
  highlighting the ``pep8`` tool and to Rick Harding for the patch.
* :issue:`314`: Test utility decorator improvements. Thanks to Rick Harding for
  initial catch & patch.


Changes in version 1.0.2 (2011-06-24)
=====================================

.. note::
    This release also includes all applicable changes from the 0.9.7 release.

Bugfixes
--------

* :issue:`258`: Bugfix to a previous, incorrectly applied fix regarding
  `~fapric.operations.local` on Windows platforms.
* :issue:`324`: Update `~fapric.operations.run`/`~fapric.operations.sudo`'s
  ``combine_stderr`` kwarg so that it correctly overrides the global setting in
  all cases. This required changing its default value to ``None``, but the
  default behavior (behaving as if the setting were ``True``) has not changed.
  Thanks to Matthew Woodcraft and Connor Smith for the catch.
* :issue:`337`: Fix logic bug in `~fapric.operations.put` preventing use of
  ``mirror_local_mode``. Thanks to Roman Imankulov for catch & patch.
* :issue:`352` (also :issue:`320`): Seemingly random issues with output lockup
  and input problems (e.g. sudo prompts incorrectly rejecting passwords) appear
  to have been caused by an I/O race condition. This has been fixed. Thanks to
  Max Arnold and Paul Oswald for the detailed reports and to Max for the
  diagnosis and patch.


Documentation
-------------

* Updated the API documentation for `~fapric.context_managers.cd` to explicitly
  point users to `~fapric.context_managers.lcd` for modifying local paths.
* Clarified the behavior of `~fapric.contrib.project.rsync_project` re: how
  trailing slashes in ``local_dir`` affect ``remote_dir``. Thanks to Mark
  Merritt for the catch.


Changes in version 1.0.1 (2011-03-27)
=====================================

.. note::
    This release also includes all applicable changes from the 0.9.5 release.

Bugfixes
--------

* :issue:`301`: Fixed a bug in `~fapric.operations.local`'s behavior when
  ``capture=False`` and ``output.stdout`` (or ``.stderr``) was also ``False``.
  Thanks to Chris Rose for the catch.
* :issue:`310`: Update edge case in `~fapric.operations.put` where using the
  ``mode`` kwarg alongside ``use_sudo=True`` runs a hidden
  `~fapric.operations.sudo` command. The ``mode`` kwarg needs to be octal but
  was being interpolated in the ``sudo`` call as a string/integer. Thanks to
  Adam Ernst for the catch and suggested fix.
* :issue:`311`: `~fapric.contrib.files.append` was supposed to have its
  ``partial`` kwarg's default flipped from ``True`` to ``False``. However, only
  the documentation was altered. This has been fixed. Thanks to Adam Ernst for
  bringing it to our attention.
* :issue:`312`: Tweak internal I/O related loops to prevent high CPU usage and
  poor screen-printing behavior on some systems. Thanks to Kirill Pinchuk for
  the initial patch.
* :issue:`320`: Some users reported problems with dropped input, particularly
  while entering `~fapric.operations.sudo` passwords. This was fixed via the
  same change as for :issue:`312`.

Documentation
-------------

* Added a missing entry for :ref:`env.path <env-path>` in the usage
  documentation.


Changes in version 1.0 (2011-03-04)
===================================

This page lists all changes made to Fapric in its 1.0.0 release.


Highlights
----------

* :issue:`7`: `~fapric.operations.run`/`~fapric.operations.sudo` now allow full
  interactivity with the remote end. You can interact with remote prompts and
  similar interfaces, making certain tasks much easier, and freeing you from
  the need to find noninteractive solutions if you don't want to. See
  :doc:`/usage/interactivity` for more on these changes.
* `~fapric.operations.put` and `~fapric.operations.get` received many updates,
  including but not limited to: recursion, globbing, inline ``sudo``
  capability, and increased control over local file paths. See the individual
  ticket line-items below for details. Erich Heine (``sophacles`` on IRC)
  played a large part in implementing and/or collecting these changes and
  deserves much of the credit.
* Added functionality for loading fapfiles which are Python packages
  (directories) instead of just modules (single files). This allows for easier
  organization of nontrivial fapfiles and paves the way for task namespacing
  in the near future. See :ref:`fapfile-discovery` for details.
* :issue:`185`: Mostly of interest to those contributing to Fapric itself,
  Fapric now leverages Paramiko to provide a stub SSH and SFTP server for use
  during runs of our test suite. This makes quick, configurable full-stack
  testing of Fapric (and, to an extent, user fapfiles) possible.


Backwards-incompatible changes
------------------------------

The below changes are **backwards incompatible** and have the potential to
break your 0.9.x based fapfiles!

* `~fapric.contrib.files.contains` and `~fapric.contrib.files.append`
  previously had the ``filename`` argument in the second position, whereas all
  other functions in the `contrib.files <fapric.contrib.files>` module had
  ``filename`` as the first argument.  These two functions have been brought in
  line with the rest of the module.
* `~fapric.contrib.files.sed` now escapes single-quotes and parentheses in
  addition to forward slashes, in its ``before`` and ``after`` kwargs. Related
  to, but not entirely contained within, :issue:`159`.
* The ``user`` and ``pty`` kwargs in `~fapric.operations.sudo`'s signature have
  had their order swapped around to more closely match
  `~fapric.operations.run`.
* As part of the changes made in :issue:`7`, `~fapric.operations.run` and
  `~fapric.operations.sudo` have had the default value of their ``pty`` kwargs
  changed from ``False`` to ``True``. This, plus the addition of the
  :ref:`combine-stderr` kwarg/env var, may result in significant behavioral
  changes in remote programs which operate differently when attached to a tty.
* :issue:`61`: `~fapric.operations.put` and `~fapric.operations.get` now honor
  the remote current-working-directory changes applied by
  `~fapric.context_managers.cd`. Previously they would always treat relative
  remote paths as being relative to the remote home directory.
* :issue:`79`: `~fapric.operations.get` now allows increased control over local
  filenames when downloading single or multiple files. This is backwards
  incompatible because the default path/filename for downloaded files has
  changed.  Thanks to Juha Mustonen, Erich Heine and Max Arnold for
  brainstorming solutions.
* :issue:`88`: `~fapric.operations.local` has changed the default value of its
  ``capture`` kwarg, from ``True`` to ``False``. This was changed in order to
  be more intuitive, at the cost of no longer defaulting to the same rich
  return value as in `~fapric.operations.run`/`~fapric.operations.sudo` (which
  is still available by specifying ``capture=True``.)
* :issue:`121`: `~fapric.operations.put` will no longer automatically attempt
  to mirror local file modes. Instead, you'll need to specify
  ``mirror_local_mode=True`` to get this behavior. Thanks to Paul Smith for a
  patch covering part of this change.
* :issue:`172`: `~fapric.contrib.files.append` has changed the default value of
  its ``partial`` kwarg from ``True`` to ``False`` in order to be safer/more
  intuitive.
* :issue:`221`: `~fapric.decorators.runs_once` now memoizes the wrapped task's
  return value and returns that value on subsequent invocations, instead of
  returning None. Thanks to Jacob Kaplan-Moss and Travis Swicegood for catch +
  patch.

Feature additions
-----------------

* Prerelease versions of Fapric (starting with the 1.0 prereleases) will now
  print the Git SHA1 hash of the current checkout, if the user is working off
  of a Git clone of the Fapric source code repository.
* Added `~fapric.context_managers.path` context manager for modifying commands'
  effective ``$PATH``.
* Added convenience ``.succeeded`` attribute to the return values of
  `~fapric.operations.run`/`~fapric.operations.sudo`/`~fapric.operations.local`
  which is simply the opposite of the ``.failed`` attribute. (This addition has
  also been backported to Fapric's 0.9 series.)
* Refactored SSH disconnection code out of the main ``fap`` loop into
  `~fapric.network.disconnect_all`, allowing library users to avoid problems
  with non-fapfile Python scripts hanging after execution finishes.
* :issue:`2`: Added ``use_sudo`` kwarg to `~fapric.operations.put` to allow
  uploading of files to privileged locations. Thanks to Erich Heine and IRC
  user ``npmap`` for suggestions and patches.
* :issue:`23`: Added `~fapric.context_managers.prefix` context manager for
  easier management of persistent state across commands.
* :issue:`27`: Added environment variable (:ref:`always-use-pty`) and
  command-line flag (:option:`--no-pty`) for global control over the
  `~fapric.operations.run`/`~fapric.operations.sudo` ``pty`` argument.
* :issue:`28`: Allow shell-style globbing in `~fapric.operations.get`. Thanks
  to Erich Heine and Max Arnold.
* :issue:`55`: `~fapric.operations.run`, `~fapric.operations.sudo` and
  `~fapric.operations.local` now provide access to their standard error
  (stderr) as an attribute on the return value, alongside e.g. ``.failed``.
* :issue:`148`: `~fapric.operations.local` now returns the same "rich" string
  object as `~fapric.operations.run`/`~fapric.operations.sudo` do, so that it
  is a string containing the command's stdout (if ``capture=True``) or the
  empty string (if ``capture=False``) which exposes the ``.failed`` and
  ``.return_code`` attributes, and so forth.
* :issue:`151`: Added a `~fapric.utils.puts` utility function, which allows
  greater control over fapfile-generated (as opposed to Fapric-generated)
  output. Also added `~fapric.utils.fastprint`, an alias to
  `~fapric.utils.puts` allowing for convenient unbuffered,
  non-newline-terminated printing.
* :issue:`192`: Added per-user/host password cache to assist in
  multi-connection scenarios.
* :issue:`193`: When requesting a remote pseudo-terminal, use the invoking
  terminal's dimensions instead of going with the default.
* :issue:`217`: `~fapric.operations.get`/`~fapric.operations.put` now accept
  file-like objects as well as local file paths for their ``local_path``
  arguments.
* :issue:`245`: Added the `~fapric.context_managers.lcd` context manager for
  controlling `~fapric.operations.local`'s current working directory and
  `~fapric.operations.put`/`~fapric.operations.get`'s local working
  directories.
* :issue:`274`: `~fapric.operations.put`/`~fapric.operations.get` now have
  return values which may be iterated over to access the paths of files
  uploaded remotely or downloaded locally, respectively. These return values
  also allow access to ``.failed`` and ``.succeeded`` attributes, just like
  `~fapric.operations.run` and friends. (In this case, ``.failed`` is actually
  a list itself containing any paths which failed to transfer, which naturally
  acts as a boolean as well.)


Documentation updates
---------------------

* API, tutorial and usage docs updated with the above new features.
* README now makes the Python 2.5+ requirement up front and explicit; some
  folks were still assuming it would run on Python 2.4.
* Added a link to Python's documentation for string interpolation in
  `~fapric.contrib.files.upload_template`'s docstring.


Changes in version 0.9.7 (2011-06-23)
=====================================

The following changes were implemented in Fapric 0.9.7:

Bugfixes
--------

* :issue:`329`: `~fapric.operations.reboot` would have problems reconnecting post-reboot (resulting in a traceback) if ``env.host_string`` was not fully-formed (did not contain user and port specifiers.) This has been fixed.


Changes in version 0.9.6 (2011-04-29)
=====================================

The following changes were implemented in Fapric 0.9.6:

Bugfixes
--------

* :issue:`347`: `~fapric.contrib.files.append` incorrectly tested for ``str``
  instead of ``types.StringTypes``, causing it to split up Unicode strings as
  if they were one character per line. This has been fixed.


Changes in version 0.9.5 (2011-03-21)
=====================================

The following changes were implemented in Fapric 0.9.5:

Bugfixes
--------

* :issue:`37`: Internal refactoring of a Paramiko call from ``_transport`` to
  ``get_transport()``.
* :issue:`258`: Modify subprocess call on Windows platforms to avoid
  space/quote problems in `~fapric.operations.local`. Thanks to Henrik
  Heimbuerger and Raymond Cote for catch + suggested fixes.
* :issue:`261`: Fix bug in `~fapric.contrib.files.comment` which truncated
  regexen ending with ``$``. Thanks to Antti Kaihola for the catch.
* :issue:`264`: Fix edge case in `~fapric.operations.reboot` by gracefully
  clearing connection cache. Thanks to Jason Gerry for the report &
  troubleshooting.
* :issue:`268`: Allow for ``@`` symbols in usernames, which is valid on some
  systems. Fapric's host-string parser now splits username and hostname at the
  last ``@`` found instead of the first. Thanks to Thadeus Burgess for the
  report.
* :issue:`287`: Fix bug in password prompt causing occasional tracebacks.
  Thanks to Antti Kaihola for the catch and Rick Harding for testing the
  proposed solution.
* :issue:`288`: Use temporary files to work around the lack of a ``-i`` flag in
  OpenBSD and NetBSD `~fapric.contrib.files.sed`. Thanks to Morgan Lefieux for
  catch + patches.
* :issue:`305`: Strip whitespace from hostnames to help prevent user error.
  Thanks to Michael Bravo for the report and Rick Harding for the patch.
* :issue:`316`: Use of `~fapric.context_managers.settings` with key names not
  previously set in ``env`` no longer raises KeyErrors. Whoops. Thanks to Adam
  Ernst for the catch.

Documentation updates
---------------------

* :issue:`228`: Added description of the PyCrypto + pip + Python 2.5 problem to
  the documentation and removed the Python 2.5 check from ``setup.py``.
* :issue:`291`: Updated the PyPM-related install docs re: recent changes in
  PyPM and its download URLs. Thanks to Sridhar Ratnakumar for the patch.


Changes in version 0.9.4 (2011-02-18)
=====================================

The following changes were implemented in Fapric 0.9.4:

Feature additions
-----------------

* Added :doc:`documentation </usage/library>` for using Fapric as a library.
* Mentioned our `Twitter account <https://twitter.com/pyfapric>`_ on the main
  docs page.
* :issue:`290`: Added ``escape`` kwarg to `~fapric.contrib.files.append` to
  allow control over previously automatic single-quote escaping.


Changes in version 0.9.3 (2010-11-12)
=====================================

The following changes were implemented in Fapric 0.9.3:

Feature additions
-----------------

* :issue:`255`: Added ``stderr`` and ``succeeded`` attributes to
  `~fapric.operations.local`.
* :issue:`254`: Backported the ``.stderr`` and ``.succeeded`` attributes on
  `~fapric.operations.run`/`~fapric.operations.sudo` return values, from the
  Git master/pre-1.0 branch. Please see those functions' API docs for details.


Bugfixes
--------

* :issue:`228`: We discovered that the pip + PyCrypto installation problem was
  limited to Python 2.5 only, and have updated our ``setup.py`` accordingly.
* :issue:`230`: Arbitrary or remainder commands (``fap <opts> -- <run command
  here>``) will no longer blow up when invoked with no fapfile present. Thanks
  to IRC user ``orkaa`` for the report.
* :issue:`242`: Empty string values in task CLI args now parse correctly.
  Thanks to Aaron Levy for the catch + patch.


Documentation updates
---------------------

* :issue:`239`: Fixed typo in execution usage docs. Thanks to Pradeep Gowda and
  Turicas for the catch.


Changes in version 0.9.2 (2010-09-06)
=====================================

The following changes were implemented in Fapric 0.9.2:

Feature additions
-----------------

* The `~fapric.operations.reboot` operation has been added, providing a way for
  Fapric to issue a reboot command and then reconnect after the system has
  restarted.
* ``python setup.py test`` now runs Fapric's test suite (provided you have all
  the prerequisites from the ``requirements.txt`` installed). Thanks to Eric
  Holscher for the patch.
* Added functionality for loading fapfiles which are Python packages
  (directories) instead of just modules (single files.) See
  :ref:`fapfile-discovery`.
* Added output lines informing the user of which tasks are being executed (e.g.
  ``[myserver] Executing task 'foo'``.)
* Added support for lazy (callable) role definition values in ``env.roledefs``.
* Added `contrib.django <fapric.contrib.django>` module with basic Django
  integration.
* :ref:`env.local_user <local-user>` was added, providing easy and permanent
  access to the local system username, even if an alternate remote username has
  been specified.
* :issue:`29`: Added support for arbitrary command-line-driven anonymous tasks
  via ``fap [options] -- [shell command]``. See :ref:`arbitrary-commands`.
* :issue:`52`: Full tracebacks during aborts are now displayed if the user has
  opted to see debug-level output.
* :issue:`101`: Added `~fapric.colors` module with basic color output support.
  (:issue:`101` is still open: we plan to leverage the new module in Fapric's
  own output in the future.)
* :issue:`137`: Commas used to separate per-task arguments may now be escaped
  with a backslash. Thanks to Erich Heine for the patch.
* :issue:`144`: `~fapric.decorators.hosts` (and `~fapric.decorators.roles`)
  will now expand a single, iterable argument instead of requiring one to use
  e.g.  ``@hosts(*iterable)``.
* :issue:`151`: Added a `~fapric.utils.puts` utility function, which allows
  greater control over fapfile-generated (as opposed to Fapric-generated)
  output. Also added `~fapric.utils.fastprint`, an alias to
  `~fapric.utils.puts` allowing for convenient unbuffered,
  non-newline-terminated printing.
* :issue:`208`: Users rolling their own shell completion or who otherwise find
  themselves performing text manipulation on the output of :option:`--list
  <-l>` may now use :option:`--shortlist` to get a plain, newline-separated
  list of task names.


Bugfixes
--------

* The interactive "what host to connect to?" prompt now correctly updates the
  appropriate environment variables (hostname, username, port) based on user
  input.
* Fixed a bug where Fapric's own internal fapfile would pre-empt the user's
  fapfile due to a PYTHONPATH order issue. User fapfiles are now always loaded
  at the front of the PYTHONPATH during import.
* Disabled some DeprecationWarnings thrown by Paramiko when that library is
  imported into Fapric under Python 2.6.
* :issue:`44`, :issue:`63`: Modified `~fapric.contrib.project.rsync_project` to
  honor the SSH port and identity file settings. Thanks to Mitch Matuson
  and Morgan Goose.
* :issue:`123`: Removed Cygwin from the "are we on Windows" test; now, only
  Python installs whose ``sys.platform`` says ``'win32'`` will use Windows-only
  code paths (e.g. importing of ``pywin32``).


Documentation updates
---------------------

* Added a few new items to the :doc:`FAQ </faq>`.
* :issue:`173`: Simple but rather embarrassing typo fix in README. Thanks to
  Ted Nyman for the catch.
* :issue:`194`: Added a note to :doc:`the install docs </installation>` about a
  possible edge case some Windows 64-bit Python users may encounter.
* :issue:`216`: Overhauled the :ref:`process backgrounding FAQ <faq-daemonize>`
  to include additional techniques and be more holistic.


Packaging updates
-----------------

* :issue:`86`, :issue:`158`: Removed the bundled Paramiko 1.7.4 and updated the
  ``setup.py`` to require Paramiko >=1.7.6. This lets us skip the known-buggy
  Paramiko 1.7.5 while getting some much needed bugfixes in Paramiko 1.7.6.


Changes in version 0.9.1 (2010-05-28)
=====================================

The following changes were implemented in Fapric 0.9.1:

Feature additions
-----------------

* :issue:`82`: `~fapric.contrib.files.append` now offers a ``partial`` kwarg
  allowing control over whether the "don't append if given text already exists"
  test looks for exact matches or not. Thanks to Jonas Nockert for the catch
  and discussion.
* :issue:`112`: ``fap --list`` now prints out the fapfile's module-level
  docstring as a header, if there is one.
* :issue:`141`: Added some more CLI args/env vars to allow user configuration
  of the Paramiko ``connect`` call -- specifically :ref:`no_agent` and
  :ref:`no_keys`.


Bugfixes
--------

* :issue:`75`: ``fap``, when called with no arguments or (useful) options, now
  prints help, even when no fapfile can be found. Previously, calling ``fap``
  in a location with no fapfile would complain about the lack of fapfile
  instead of displaying help.
* :issue:`130`: Context managers now correctly clean up ``env`` if they
  encounter an exception. Thanks to Carl Meyer for catch + patch.
* :issue:`132`: `~fapric.operations.local` now calls ``strip`` on its stdout,
  matching the behavior of `~fapric.operations.run`/`~fapric.operations.sudo`.
  Thanks to Carl Meyer again on this one.
* :issue:`166`: `~fapric.context_managers.cd` now correctly overwrites
  ``env.cwd`` when given an absolute path, instead of naively appending its
  argument to ``env.cwd``'s previous value.


Documentation updates
---------------------

* A number of small to medium documentation tweaks were made which had no
  specific Redmine ticket. The largest of these is the addition of :doc:`the
  FAQ <../faq>` to the Sphinx documentation instead of storing it as a
  source-only text file. (Said FAQ was also slightly expanded with new FAQs.)
* :issue:`17`: Added :ref:`note to FAQ <faq-daemonize>` re: use of ``dtach`` as
  alternative to ``screen``. Thanks to Erich Heine for the tip.
* :issue:`64`: Updated :ref:`installation docs <downloads>` to clarify where
  package maintainers should be downloading tarballs from. Thanks to James
  Pearson for providing the necessary perspective.
* :issue:`95`: Added a link to a given version's changelog on the PyPI page
  (technically, to the ``setup.py`` ``long_description`` field).
* :issue:`110`: Alphabetized :ref:`the CLI argument command reference
  <command-line-options>`. Thanks to Erich Heine.
* :issue:`120`: Tweaked documentation, help strings to make it more obvious
  that fapfiles are simply Python modules.
* :issue:`127`: Added :ref:`note to install docs <pypm>` re: ActiveState's
  PyPM. Thanks to Sridhar Ratnakumar for the tip. 


Changes in version 0.9 (2009-11-08)
===================================

This document details the various backwards-incompatible changes made during
Fapric's rewrite between versions 0.1 and 0.9. The codebase has been almost
completely rewritten and reorganized and an attempt has been made to remove
"magical" behavior and make things more simple and Pythonic; the ``fap``
command-line component has also been redone to behave more like a typical Unix
program.


Major changes
-------------

You'll want to at least skim the entire document, but the primary changes that
will need to be made to one's fapfiles are as follows:

Imports
~~~~~~~

You will need to **explicitly import any and all methods or decorators used**,
at the top of your fapfile; they are no longer magically available. Here's a
sample fapfile that worked with 0.1 and earlier::

     @hosts('a', 'b')
     def my_task():
         run('ls /var/www')
         sudo('mkdir /var/www/newsite')

The above fapfile uses `hosts`, `run` and `sudo`, and so in Fapric 0.9 one
simply needs to import those objects from the new API module ``fapric.api``::

     from fapric.api import hosts, run, sudo

     @hosts('a', 'b')
     def my_task():
         run('ls /var/www')
         sudo('mkdir /var/www/newsite')

You may, if you wish, use ``from fapric.api import *``, though this is
technically not Python best practices; or you may import directly from the
Fapric submodules (e.g. ``from fapric.decorators import hosts``.)
See :doc:`../usage/fapfiles` for more information.

Python version
~~~~~~~~~~~~~~

Fapric started out Python 2.5-only, but became largely 2.4 compatible at one
point during its lifetime. Fapric is once again **only compatible with Python
2.5 or newer**, in order to take advantage of the various new features and
functions available in that version.

With this change we're setting an official policy to support the two most
recent stable releases of the Python 2.x line, which at time of writing is 2.5
and 2.6. We feel this is a decent compromise between new features and the
reality of operating system packaging concerns. Given that most users use
Fapric from their workstations, which are typically more up-to-date than
servers, we're hoping this doesn't cut out too many folks.

Finally, note that while we will not officially support a 2.4-compatible
version or fork, we may provide a link to such a project if one arises.

Environment/config variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``config`` object previously used to access and set internal state
(including Fapric config options) **has been renamed** to :data:`env`, but
otherwise remains mostly the same (it allows both dictionary and
object-attribute style access to its data.) :data:`env` resides in the
:mod:`state` submodule and is importable via ``fapric.api``, so where before
one might have seen fapfiles like this::

    def my_task():
        config.foo = 'bar'

one will now be explicitly importing the object like so::

    from fapric.api import env

    def my_task():
        env.foo = 'bar'

Execution mode
~~~~~~~~~~~~~~

Fapric's default mode of use, in prior versions, was what we called "broad
mode": your tasks, as Python code, ran only once, and any calls to functions
that made connections (such as `run` or `sudo`) would run once per host in the
current host list. We also offered "deep mode", in which your entire task
function would run once per host.

In Fapric 0.9, this dichotomy has been removed, and **"deep mode" is the
method Fapric uses to perform all operations**. This allows you to treat your
Fapfiles much more like regular Python code, including the use of ``if``
statements and so forth, and allows operations like `run` to unambiguously
return the output from the server.

Other modes of execution such as the old "broad mode" may return as Fapric's
internals are refactored and expanded, but for now we've simplified things, and
deep mode made the most sense as the primary mode of use.

"Lazy" string interpolation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because of how Fapric used to run in "broad mode" (see previous section) a
special string formatting technique -- the use of a bash-like dollar sign
notation, e.g. ``"hostname: $(fap_host)"`` -- had to be used to allow the
current state of execution to be represented in one's operations. **This is no
longer necessary and has been removed**. Because your tasks are executed once
per host, you may build strings normally (e.g. with the ``%`` operator) and
refer to ``env.host_string``, ``env.user`` and so forth.

For example, Fapric 0.1 had to insert the current username like so::

    print("Your current username is $(fap_user)")

Fapric 0.9 and up simply reference ``env`` variables as normal::

    print("Your current username is %s" % env.user)

As with the execution modes, a special string interpolation function or method
that automatically makes use of ``env`` values may find its way back into
Fapric at some point if a need becomes apparent.


Other backwards-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In no particular order:

* The Fapric config file location used to be ``~/.fapric``; in the interests
  of honoring Unix filename conventions, it's now ``~/.fapricrc``.

* The old ``config`` object (now :data:`env`) had a ``getAny`` method which
  took one or more key strings as arguments, and returned the value attached
  to the first valid key. This method still exists but has been renamed to
  `first`.

* Environment variables such as ``fap_host`` have been renamed to simply e.g.
  ``host``. This looks cleaner and feels more natural, and requires less
  typing. Users will naturally need to be careful not to override these
  variables, but the same holds true for e.g. Python's builtin methods and
  types already, so we felt it was worth the tradeoff.

* Fapric's version header is no longer printed every time the program runs;
  you should now use the standard ``--version``/``-V`` command-line options to
  print version and exit.

* The old ``about`` command has been removed; other Unix programs don't
  typically offer this. Users can always view the license and warranty info in
  their respective text files distributed with the software.

* The old ``help`` command is now the typical Unix options ``-h``/``--help``.

    * Furthermore, there is no longer a listing of Fapric's programming API
      available through the command line -- those topics impact fapfile
      authors, not fap users (even though the former is a subset of the
      latter) and should stay in the documentation only.

* `prompt`'s primary function is now to return a value to the caller, although
  it may still optionally store the entered value in `env` as well.

* `prompt` now considers the empty string to be valid input; this allows other
  functions to wrap `prompt` and handle "empty" input on their own terms.

* In addition to the above changes, `prompt` has been updated to behave more
  obviously, as its previous behavior was confusing in a few ways:

    * It will now overwrite pre-existing values in the environment dict, but
      will print a warning to the user if it does so.

    * Additionally, (and this appeared to be undocumented) the ``default``
      argument could take a callable as well as a string, and would simply set
      the default message to the return value if a callable was given. This
      seemed to add unnecessary complexity (given that users may call e.g.
      ``prompt(blah, msg, default=my_callable()``) so it has been removed.

* When connecting, Fapric used to use the undocumented ``fap_pkey`` env
  variable as a method of passing in a Paramiko ``PKey`` object to the SSH
  client's ``connect`` method. This has been removed in favor of an
  ``ssh``-like ``-i`` option, which allows one to specify a private key file
  to use; that should generally be enough for most users.

* ``download`` is now `get` in order to match up with `put` (the name mismatch
  was due to `get` being the old method of getting env vars.)

* The ``noshell`` argument to `sudo` (added late in its life to previous
  Fapric versions) has been renamed to ``shell`` (defaults to True, so the
  effective behavior remains the same) and has also been extended to the `run`
  operation.

    * Additionally, the global ``sudo_noshell`` option has been renamed to
      ``use_shell`` and also applies to both `run` and `sudo`.

* ``local_per_host`` has been removed, as it only applied to the now-removed
  "broad mode".

* ``load`` has been removed; Fapric is now "just Python", so use Python's
  import mechanisms in order to stitch multiple fapfiles together.

* ``abort`` is no longer an "operation" *per se* and has been moved to
  :mod:`fapric.utils`. It is otherwise the same as before, taking a single
  string message, printing it to the user and then calling ``sys.exit(1)``.

* ``rsyncproject`` and ``upload_project`` have been moved into
  :mod:`fapric.contrib` (specifically, :mod:`fapric.contrib.project`), which
  is intended to be a new tree of submodules for housing "extra" code which
  may build on top of the core Fapric operations.

* ``invoke`` has been turned on its head, and is now the `runs_once` decorator
  (living in :mod:`fapric.decorators`). When used to decorate a function, that
  function will only execute one time during the lifetime of a ``fap`` run.
  Thus, where you might have used ``invoke`` multiple times to ensure a given
  command only runs once, you may now use `runs_once` to decorate the function
  and then call it multiple times in a normal fashion.

* It looks like the regex behavior of the ``validate`` argument to `prompt`
  was never actually implemented. It now works as advertised.

* Couldn't think of a good reason for `require` to be a decorator *and* a
  function, and the function is more versatile in terms of where it may be
  used, so the decorator has been removed.

* As things currently stand with the execution model, the ``depends``
  decorator doesn't make a lot of sense: instead, it's safest/best to simply
  make "meta" commands that just call whatever chain of "real" commands you
  need performed for a given overarching task.

  For example, instead of having command A say
  that it "depends on" command B, create a command C which calls A and B in the
  right order, e.g.::

    def build():
        local('make clean all')

    def upload():
        put('app.tgz', '/tmp/app.tgz')
        run('tar xzf /tmp/app.tgz')

    def symlink():
        run('ln -s /srv/media/photos /var/www/app/photos')

    def deploy():
        build()
        upload()
        symlink()

  .. note::

    The execution model is still subject to change as Fapric evolves. Please
    don't hesitate to email the list or the developers if you have a use case
    that needs something Fapric doesn't provide right now!

* Removed the old ``fap shell`` functionality, since the move to "just Python"
  should make vanilla ``python``/``ipython`` usage of Fapric much easier.

    * We may add it back in later as a convenient shortcut to what basically
      amounts to running ``ipython`` and performing a handful of ``from
      fapric.foo import bar`` calls.

* The undocumented `fap_quiet` option has been replaced by a much more granular
  set of output controls. For more info, see :doc:`../usage/output_controls`.


Changes from alpha 1 to alpha 2
-------------------------------

The below list was generated by running ``git shortlog 0.9a1..0.9a2`` and then
manually sifting through and editing the resulting commit messages. This will
probably occur for the rest of the alphas and betas; we hope to use
Sphinx-specific methods of documenting changes once the final release is out
the door.

* Various minor tweaks to the (still in-progress) documentation, including one
  thanks to Curt Micol.
  
* Added a number of TODO items based on user feedback (thanks!)

* Host information now available in granular form (user, host, port) in the
  env dict, alongside the full ``user@host:port`` host string.

* Parsing of host strings is now more lenient when examining the username
  (e.g. hyphens.)

* User/host info no longer cleared out between commands.

* Tweaked ``setup.py`` to use ``find_packages``. Thanks to Pat McNerthney.

* Added 'capture' argument to `~fapric.operations.local` to allow local
  interactive tasks.

* Reversed default value of `~fapric.operations.local`'s ``show_stderr``
  kwarg; local stderr now prints by default instead of being hidden by
  default.

* Various internal fapfile tweaks.


Changes from alpha 2 to alpha 3
-------------------------------

* Lots of updates to the documentation and TODO

* Added contrib.files with a handful of file-centric subroutines

* Added contrib.console for console UI stuff (so far, just `confirm`)

* Reworked config file mechanisms a bit, added CLI flag for setting it.

* Output controls (including CLI args, documentation) have been added

* Test coverage tweaked and grown a small amount (thanks in part to Peter
  Ellis)

* Roles overhauled/fixed (more like hosts now)

* Changed ``--list`` linewrap behavior to truncate instead.

* Make private key passphrase prompting more obvious to users.

* Add ``pty`` option to `sudo`. Thanks to José Muanis for the tip-off re: get_pty()

* Add CLI argument for setting the shell used in commands (thanks to Steve Steiner)

* Only load host keys when ``env.reject_unknown_keys`` is True. Thanks to Pat
  McNerthney.

* And many, many additional bugfixes and behavioral tweaks too small to merit
  cluttering up this list! Thanks as always to everyone who contributed
  bugfixes, feedback and/or patches.


Changes from alpha 3 to beta 1
------------------------------

This is closer to being a straight dump of the Git changelog than the previous
sections; apologies for the overall change in tense.

* Add autodocs for fapric.contrib.console.

* Minor cleanup to package init and setup.py.

* Handle exceptions with strerror attributes that are None instead of strings.

* contrib.files.append may now take a list of strings if desired.

* Straighten out how prompt() deals with trailing whitespace

* Add 'cd' context manager.

* Update upload_template to correctly handle backing up target directories.

* upload_template() can now use Jinja2 if it's installed and user asks for it.

* Handle case where remote host SSH key doesn't match known_hosts.

* Fix race condition in run/sudo.

* Start fledgling FAQ; extended pty option to run(); related doc tweaks.

* Bring local() in line with run()/sudo() in terms of .failed attribute.

* Add dollar-sign backslash escaping to run/sudo.

* Add FAQ question re: backgrounding processes.

* Extend some of put()'s niceties to get(), plus docstring/comment updates

* Add debug output of chosen fapfile for troubleshooting fapfile discovery.

* Fix Python path bug which sometimes caused Fapric's internal fapfile to
  pre-empt user's fapfile during load phase.

* Gracefully handle "display" for tasks with no docstring.

* Fix edge case that comes up during some auth/prompt situations.

* Handle carriage returns in output_thread correctly. Thanks to Brian Rosner.


Changes from beta 1 to release candidate 1
------------------------------------------

As with the previous changelog, this is also mostly a dump of the Git log. We
promise that future changelogs will be more verbose :)

* Near-total overhaul and expansion of documentation (this is the big one!)
  Other mentions of documentation in this list are items deserving their own
  mention, e.g. FAQ updates.
* Add FAQ question re: passphrase/password prompt
* Vendorized Paramiko: it is now included in our distribution and is no longer
  an external dependency, at least until upstream fixes a nasty 1.7.5 bug.
* Fix #34: switch upload_template to use mkstemp (also removes Python 2.5.2+
  dependency -- now works on 2.5.0 and up)
* Fix #62 by escaping backticks.
* Replace "ls" with "test" in exists()
* Fixes #50. Thanks to Alex Koshelev for the patch.
* ``local``'s return value now exhibits ``.return_code``.
* Abort on bad role names instead of blowing up.
* Turn off DeprecationWarning when importing paramiko.
* Attempted fix re #32 (dropped output)
* Update role/host initialization logic (was missing some edge cases)
* Add note to install docs re: PyCrypto on win32.
* Add FAQ item re: changing env.shell.
* Rest of TODO migrated to tickets.
* ``fap test`` (when in source tree) now uses doctests.
* Add note to compatibility page re: fap_quiet.
* Update local() to honor context_managers.cd()

Changes from release candidate 1 to final release
-------------------------------------------------

* Fixed the `~fapric.contrib.files.sed` docstring to accurately reflect which
  ``sed`` options it uses.
* Various changes to internal fapfile, version mechanisms, and other
  non-user-facing things.
