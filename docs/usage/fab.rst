=============================
``fab`` options and arguments
=============================

The most common method for utilizing Fabric is via its command-line tool,
``fab``, which should have been placed on your shell's executable path when
Fabric was installed. ``fab`` tries hard to be a good Unix citizen, using a
standard style of command-line switches, help output, and so forth.


Basic use
=========

In its most simple form, ``fab`` may be called with no options at all, and
with one or more arguments, which should be task names, e.g.::

    $ fab task1 task2

As detailed in :doc:`../tutorial` and :doc:`execution`, this will run ``task1``
followed by ``task2``, assuming that Fabric was able to find a fabfile nearby
containing Python functions with those names.

However, it's possible to expand this simple usage into something more
flexible, by using the provided options and/or passing arguments to individual
tasks.


Command-line options
====================

A quick overview of all possible command line options can be found via ``fab
--help``. If you're looking for details on a specific option, we go into detail
below.

``-h/--help``
-------------

Displays a standard help message, with all possible options and a brief
overview of what they do, then exits.

``-V/--version``
----------------

Displays Fabric's version number, then exits. Note that the shorthand form is a
capital ``V``, not a lowercase one.

``-l/--list``
-------------

Imports a fabfile as normal, but then prints a list of all discovered tasks and
exits. If provided, will print the first line of each task's docstring next to
it (truncating if necessary.)

``-d COMMAND/--display=COMMAND``
--------------------------------

Prints the entire docstring for the given task, if there is one. Does not
currently print out the task's function signature, so descriptive docstrings
are a good idea. (They're *always* a good idea, of course -- just moreso here.)

``-r/--reject-unknown-hosts``
-----------------------------

Sets :ref:`env.reject_unknown_hosts <reject-unknown-hosts>` to ``True``,
causing Fabric to abort when connecting to hosts not found in the user's SSH
known_hosts file.

``-D/--disable-known-hosts``
----------------------------

Sets :ref:`env.disable_known_hosts <disable-known-hosts>` to ``True``,
preventing Fabric from loading the user's SSH known_hosts file.

``-u USER/--user=USER``
-----------------------

Sets :ref:`env.user <user>` to the given string; it will then be used as the
default username when making SSH connections.

``-p PASSWORD/--password=PASSWORD``
-----------------------------------

Sets :ref:`env.password <password>` to the given string; it will then be used
as the default password when making SSH connections or calling the ``sudo``
program.

``-H HOSTS/--hosts=HOSTS``
--------------------------

Sets :ref:`env.hosts <hosts>` to the given comma-delimited list of host
strings.

``-R ROLES/--roles=ROLES``
--------------------------

Sets :ref:`env.roles <roles>` to the given comma-separated list of role names.

``-i KEY_FILENAME``
-------------------

When set to a file path, will load the given file as an SSH identity file
(usually a private key.) This option may be repeated multiple times.

``-f FABFILE/--fabfile=FABFILE``
--------------------------------

The fabfile name pattern to search for (defaults to ``fabfile.py``), or
alternately an explicit file path to load as the fabfile (e.g.
``/path/to/my/fabfile.py``.)

.. seealso:: :doc:`fabfiles`

``-w/--warn-only``
------------------

Sets :ref:`env.warn_only <warn_only>` to ``True``, causing Fabric to continue
execution even when commands encounter error conditions.

``-s SHELL/--shell=SHELL``
--------------------------

Sets :ref:`env.shell <shell>` to the given string, overriding the default shell
wrapper used to execute remote commands.

.. seealso:: `~fabric.operations.run`, `~fabric.operations.sudo`

``-c RCFILE/--config=RCFILE``
-----------------------------

Sets :ref:`env.rcfile <rcfile>` to the given file path, which Fabric will try
to load on startup and use to update environment variables.

``--hide=LEVELS``
-----------------

A comma-separated list of :doc:`output levels <output_controls>` to hide by
default.

``--show=LEVELS``
-----------------

A comma-separated list of :doc:`output levels <output_controls>` to show by
default.


Per-task arguments
==================

Move some docstrings in here.


Settings files
==============

Talk about RCfiles here.
