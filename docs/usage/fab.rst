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


.. _arbitrary-commands:

Arbitrary remote shell commands
===============================

.. versionadded:: 0.9.2

Fabric leverages a lesser-known command line convention and may be called in
the following manner::

    $ fab [options] -- [shell command]

where everything after the ``--`` is turned into a temporary
`~fabric.operations.run` call, and is not parsed for ``fab`` options. If you've
defined a host list at the module level or on the command line, this usage will
act like a one-line anonymous task.

For example, let's say you just wanted to get the kernel info for a bunch of
systems; you could do this::

    $ fab -H system1,system2,system3 -- uname -a

which would be literally equivalent to the following fabfile::

    from fabric.api import run

    def anonymous():
        run("uname -a")

as if it were executed thusly::

    $ fab -H system1,system2,system3 anonymous

Most of the time you will want to just write out the task in your fabfile
(anything you use once, you're likely to use again) but this feature provides a
handy, fast way to quickly dash off an SSH-borne command while leveraging your
fabfile's connection settings.


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

    Sets :ref:`env.no_agent <no_agent>` to ``True``, forcing our SSH layer not
    to talk to the SSH agent when trying to unlock private key files.

    .. versionadded:: 0.9.1

.. cmdoption:: --abort-on-prompts

    Sets :ref:`env.abort_on_prompts <abort-on-prompts>` to ``True``, forcing
    Fabric to abort whenever it would prompt for input.

    .. versionadded:: 1.1

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

.. cmdoption:: -F LIST_FORMAT, --list-format=LIST_FORMAT

    Allows control over the output format of :option:`--list <-l>`. ``short`` is
    equivalent to :option:`--shortlist`, ``normal`` is the same as simply
    omitting this option entirely (i.e. the default), and ``nested`` prints out
    a nested namespace tree.

    .. versionadded:: 1.1
    .. seealso:: :option:`--shortlist`, :option:`--list <-l>`

.. cmdoption:: -h, --help

    Displays a standard help message, with all possible options and a brief
    overview of what they do, then exits.

.. cmdoption:: --hide=LEVELS

    A comma-separated list of :doc:`output levels <output_controls>` to hide by
    default.


.. cmdoption:: -H HOSTS, --hosts=HOSTS

    Sets :ref:`env.hosts <hosts>` to the given comma-delimited list of host
    strings.

.. cmdoption:: -x HOSTS, --exclude-hosts=HOSTS

    Sets :ref:`env.exclude_hosts <exclude-hosts>` to the given comma-delimited
    list of host strings to then keep out of the final host list.

    .. versionadded:: 1.1

.. cmdoption:: -i KEY_FILENAME

    When set to a file path, will load the given file as an SSH identity file
    (usually a private key.) This option may be repeated multiple times. Sets
    (or appends to) :ref:`env.key_filename <key-filename>`.

.. cmdoption:: -k

    Sets :ref:`env.no_keys <no_keys>` to ``True``, forcing the SSH layer to not
    look for SSH private key files in one's home directory.

    .. versionadded:: 0.9.1

.. cmdoption:: --keepalive=KEEPALIVE

    Sets :ref:`env.keepalive <keepalive>` to the given (integer) value, specifying an SSH keepalive interval.

    .. versionadded:: 1.1

.. cmdoption:: --linewise

    Forces output to be buffered line-by-line instead of byte-by-byte. Often useful or required for :ref:`parallel execution <linewise-output>`.

    .. versionadded:: 1.3

.. cmdoption:: -l, --list

    Imports a fabfile as normal, but then prints a list of all discovered tasks
    and exits. Will also print the first line of each task's docstring, if it
    has one, next to it (truncating if necessary.)

    .. versionchanged:: 0.9.1
        Added docstring to output.
    .. seealso:: :option:`--shortlist`, :option:`--list-format <-F>`

.. cmdoption:: -p PASSWORD, --password=PASSWORD

    Sets :ref:`env.password <password>` to the given string; it will then be
    used as the default password when making SSH connections or calling the
    ``sudo`` program.

.. cmdoption:: -P, --parallel

    Sets :ref:`env.parallel <env-parallel>` to ``True``, causing
    tasks to run in parallel.

    .. versionadded:: 1.3
    .. seealso:: :doc:`/usage/parallel`

.. cmdoption:: --no-pty

    Sets :ref:`env.always_use_pty <always-use-pty>` to ``False``, causing all
    `~fabric.operations.run`/`~fabric.operations.sudo` calls to behave as if
    one had specified ``pty=False``.

    .. versionadded:: 1.0

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

.. cmdoption:: --shortlist

    Similar to :option:`--list <-l>`, but without any embellishment, just task
    names separated by newlines with no indentation or docstrings.

    .. versionadded:: 0.9.2
    .. seealso:: :option:`--list <-l>`

.. cmdoption:: --show=LEVELS

    A comma-separated list of :doc:`output levels <output_controls>` to
    be added to those that are shown by
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

.. cmdoption:: -z, --pool-size

    Sets :ref:`env.pool_size <pool-size>`, which specifies how many processes
    to run concurrently during parallel execution.

    .. versionadded:: 1.3
    .. seealso:: :doc:`/usage/parallel`


.. _task-arguments:

Per-task arguments
==================

The options given in :ref:`command-line-options` apply to the invocation of
``fab`` as a whole; even if the order is mixed around, options still apply to
all given tasks equally. Additionally, since tasks are just Python functions,
it's often desirable to pass in arguments to them at runtime.

Answering both these needs is the concept of "per-task arguments", which is a
special syntax you can tack onto the end of any task name:

* Use a colon (``:``) to separate the task name from its arguments;
* Use commas (``,``) to separate arguments from one another (may be escaped
  by using a backslash, i.e. ``\,``);
* Use equals signs (``=``) for keyword arguments, or omit them for positional
  arguments. May also be escaped with backslashes.

Additionally, since this process involves string parsing, all values will end
up as Python strings, so plan accordingly. (We hope to improve upon this in
future versions of Fabric, provided an intuitive syntax can be found.)

For example, a "create a new user" task might be defined like so (omitting most
of the actual logic for brevity)::

    def new_user(username, admin='no', comment="No comment provided"):
        log_action("New User (%s): %s" % (username, comment))
        pass

You can specify just the username::

    $ fab new_user:myusername

Or treat it as an explicit keyword argument::

    $ fab new_user:username=myusername

If both args are given, you can again give them as positional args::

    $ fab new_user:myusername,yes

Or mix and match, just like in Python::

    $ fab new_user:myusername,admin=yes

The ``log_action`` call above is useful for illustrating escaped commas, like
so::

    $ fab new_user:myusername,admin=no,comment='Gary\, new developer (starts Monday)'

.. note::
    Quoting the backslash-escaped comma is required, as not doing so will cause
    shell syntax errors. Quotes are also needed whenever an argument involves
    other shell-related characters such as spaces.

All of the above are translated into the expected Python function calls. For
example, the last call above would become::

    >>> new_user('myusername', admin='yes', comment='Gary, new developer (starts Monday)')

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
