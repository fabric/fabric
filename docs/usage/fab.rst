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


.. _command-line-options:

Command-line options
====================

A quick overview of all possible command line options can be found via ``fab
--help``. If you're looking for details on a specific option, we go into detail
below.

.. note::

    ``fab`` uses Python's `optparse`_ library, meaning that it honors typical
    Linux or GNU style short and long options, as well as freely mixing options
    and arguments. E.g. ``fab task1 -H hostname task2 -i path/to/keyfile`` is
    just as valid as the more straightforward ``fab -H hostname -i
    path/to/keyfile task1 task2``.

.. _optparse: http://docs.python.org/library/optparse.html

.. cmdoption:: -a

    Sets :ref:`env.no_agent <no_agent>` to ``True``, forcing Paramiko not to
    talk to the SSH agent when trying to unlock private key files.

    .. versionadded:: 0.9.1

.. cmdoption:: -c RCFILE, --config=RCFILE

    Sets :ref:`env.rcfile <rcfile>` to the given file path, which Fabric will
    try to load on startup and use to update environment variables.

.. cmdoption:: -d COMMAND, --display=COMMAND

    Prints the entire docstring for the given task, if there is one. Does not
    currently print out the task's function signature, so descriptive
    docstrings are a good idea. (They're *always* a good idea, of course --
    just moreso here.)

.. cmdoption:: -D, --disable-known-hosts

    Sets :ref:`env.disable_known_hosts <disable-known-hosts>` to ``True``,
    preventing Fabric from loading the user's SSH known_hosts file.

.. cmdoption:: -f FABFILE, --fabfile=FABFILE

    The fabfile name pattern to search for (defaults to ``fabfile.py``), or
    alternately an explicit file path to load as the fabfile (e.g.
    ``/path/to/my/fabfile.py``.)

.. seealso:: :doc:`fabfiles`

.. cmdoption:: -h, --help

    Displays a standard help message, with all possible options and a brief
    overview of what they do, then exits.

.. cmdoption:: --hide=LEVELS

    A comma-separated list of :doc:`output levels <output_controls>` to hide by
    default.


.. cmdoption:: -H HOSTS, --hosts=HOSTS

    Sets :ref:`env.hosts <hosts>` to the given comma-delimited list of host
    strings.

.. cmdoption:: -i KEY_FILENAME

    When set to a file path, will load the given file as an SSH identity file
    (usually a private key.) This option may be repeated multiple times. Sets
    (or appends to) :ref:`env.key_filename <key-filename>`.

.. cmdoption:: -k

    Sets :ref:`env.no_keys <no_keys>` to ``True``, forcing Paramiko to not look
    for SSH private key files in one's home directory.

    .. versionadded:: 0.9.1

.. cmdoption:: -l, --list

    Imports a fabfile as normal, but then prints a list of all discovered tasks
    and exits. Will also print the first line of each task's docstring, if it
    has one, next to it (truncating if necessary.)

    .. versionchanged:: 0.9.1
        Added docstring to output.

.. cmdoption:: -p PASSWORD, --password=PASSWORD

    Sets :ref:`env.password <password>` to the given string; it will then be
    used as the default password when making SSH connections or calling the
    ``sudo`` program.

.. cmdoption:: -r, --reject-unknown-hosts

    Sets :ref:`env.reject_unknown_hosts <reject-unknown-hosts>` to ``True``,
    causing Fabric to abort when connecting to hosts not found in the user's SSH
    known_hosts file.

.. cmdoption:: -R ROLES, --roles=ROLES

    Sets :ref:`env.roles <roles>` to the given comma-separated list of role
    names.

.. cmdoption:: -s SHELL, --shell=SHELL

    Sets :ref:`env.shell <shell>` to the given string, overriding the default
    shell wrapper used to execute remote commands.

.. cmdoption:: --show=LEVELS

    A comma-separated list of :doc:`output levels <output_controls>` to show by
    default.

.. seealso:: `~fabric.operations.run`, `~fabric.operations.sudo`

.. cmdoption:: -u USER, --user=USER

    Sets :ref:`env.user <user>` to the given string; it will then be used as the
    default username when making SSH connections.

.. cmdoption:: -V, --version

    Displays Fabric's version number, then exits.

.. cmdoption:: -w, --warn-only

    Sets :ref:`env.warn_only <warn_only>` to ``True``, causing Fabric to
    continue execution even when commands encounter error conditions.

Per-task arguments
==================

The options given in :ref:`command-line-options` apply to the invocation of
``fab`` as a whole; even if the order is mixed around, options still apply to
all given tasks equally. Additionally, since tasks are just Python functions,
it's often desirable to pass in arguments to them at runtime.

Answering both these needs is the concept of "per-task arguments", which is a
special syntax you can tack onto the end of any task name:

* Use a colon (``:``) to separate the task name from its arguments;
* Use commas (``,``) to separate arguments from one another;
* Use equals signs (``=``) for keyword arguments, or omit them for positional
  arguments;

Additionally, since this process involves string parsing, all values will end
up as Python strings, so plan accordingly. (We hope to improve upon this in
future versions of Fabric, provided an intuitive syntax can be found.)

For example, a "create a new user" task might be defined like so (omitting the
actual logic for brevity)::

    def new_user(username, admin='no'):
        pass

You can specify just the username::

    $ fab new_user:myusername

Or treat it as an explicit keyword argument::

    $ fab new_user:username=myusername

If both args are given, you can again give them as positional args::

    $ fab new_user:myusername,yes

Or mix and match, just like in Python::

    $ fab new_user:myusername,admin=yes

All of the above are translated into the expected Python function calls. For
example, the last call above would become::

    >>> new_user('myusername', admin='yes')

Roles and hosts
---------------

As mentioned in :ref:`the section on task execution <hosts-per-task-cli>`,
there are a handful of per-task keyword arguments (``host``, ``hosts``,
``role`` and ``roles``) which do not actually map to the task functions
themselves, but are used for setting per-task host and/or role lists.

These special kwargs are **removed** from the args/kwargs sent to the task
function itself; this is so that you don't run into TypeErrors if your task
doesn't define the kwargs in question. (It also means that if you **do** define
arguments with these names, you won't be able to specify them in this manner --
a regrettable but necessary sacrifice.)

.. note::

    If both the plural and singular forms of these kwargs are given, the value
    of the plural will win out and the singular will be discarded.

When using the plural form of these arguments, one must use semicolons (``;``)
since commas are already being used to separate arguments from one another.
Furthermore, since your shell is likely to consider semicolons a special
character, you'll want to quote the host list string to prevent shell
interpretation, e.g.::

    $ fab new_user:myusername,hosts="host1;host2"

Again, since the ``hosts`` kwarg is removed from the argument list sent to the
``new_user`` task function, the actual Python invocation would be
``new_user('myusername')``, and the function would be executed on a host list
of ``['host1', 'host2']``.

.. _fabricrc:

Settings files
==============

Fabric currently honors a simple user settings file, or ``fabricrc`` (think
``bashrc`` but for ``fab``) which should contain one or more key-value pairs,
one per line. These lines will be subject to ``string.split('=')``, and thus
can currently only be used to specify string settings. Any such key-value pairs
will be used to update :doc:`env <env>` when ``fab`` runs, and is loaded prior
to the loading of any fabfile.

By default, Fabric looks for ``~/.fabricrc``, and this may be overridden by
specifying the :option:`-c` flag to ``fab``.

For example, if your typical SSH login username differs from your workstation
username, and you don't want to modify ``env.user`` in a project's fabfile
(possibly because you expect others to use it as well) you could write a
``fabricrc`` file like so::

    user = ssh_user_name

Then, when running ``fab``, your fabfile would load up with ``env.user`` set to
``'ssh_user_name'``. Other users of that fabfile could do the same, allowing
the fabfile itself to be cleanly agnostic regarding the default username.
