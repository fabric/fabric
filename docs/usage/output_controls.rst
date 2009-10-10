===============
Managing output
===============



Output controls
---------------

Fabric is verbose by default, allowing you to see what's going on at any given
moment: it prints out which tasks it's executing, what local/remote commands
are running, which files are up- or downloading, and the contents of the remote
end's standard output and error.

However, in many situations this verbosity can result in a large amount of
output, and to help you handle it, Fabric provides two context managers:
`~fabric.context_managers.hide` and `~fabric.context_managers.show`. These take
one or more strings naming various output groups to hide or show, respectively.

Building upon an earlier example, the below shows how the contrib
`~fabric.contrib.files.exists` function can hide the normal ``[run] test -e
<path>`` line, and its standard output, so as to not clutter up your terminal
during a simple operation::

    from fabric.api import settings, run, hide

    def exists(path):
        with settings(hide('running', 'stdout'), warn_only=True):
            return run('test -e %s' % path)

.. note::

    While `~fabric.context_managers.hide` is a standalone context manager, we
    use it here inside of `~fabric.context_managers.settings`, which is capable
    of combining other context managers as well as performing its own function.
    This helps prevent your fabfile from having too many indent levels.

See :doc:`output_controls` for details on the various output levels available, as
well as further notes on the use of `~fabric.context_managers.hide` and
`~fabric.context_managers.show`.







Output controls
===============

The ``fab`` tool is very verbose by default and prints out almost everything it
can, including the remote end's stderr and stdout streams, the command strings
being executed, and so forth. While this is necessary in many cases in order to
know just what's going on, any nontrivial Fabric task will quickly become
difficult to follow as it runs.

To solve this problem, Fabric allows granular control over its output, which is
grouped into the following levels:

* **status**: Status messages, i.e. noting when Fabric is done running, if
  the user used a keyboard interrupt, or when servers are disconnected from.
  These messages are almost always necessary and rarely verbose.

* **aborts**: Abort messages. Like status messages, these should really only be
  turned off when using Fabric as a library, and possibly not even then. Note
  that even if this output group is turned off, aborts will still occur --
  there just won't be any output about why Fabric aborted!

* **warnings**: Warning messages. These are often turned off when one expects a
  given operation to fail, such as when using ``grep`` to test existence of
  text in a file. If paired with setting ``env.warn_only`` to True, this
  results in fully silent warnings when remote programs fail. As with
  ``aborts``, this setting does not control actual warning behavior, only
  whether warning messages are printed or hidden.

* **running**: Printouts of commands being executed or files transferred, e.g.
  ``[myserver] run: ls /var/www``.

* **stdout**: Local, or remote, stdout, i.e. non-error output from commands.

* **stderr**: Local, or remote, stderr, i.e. error-related output from commands.

* **debug**: Turn on debugging. Typically off; used to see e.g. the "full"
  commands being run (i.e. where before you would only see the command as
  passed to `run`, with debugging on you would see the full ``/bin/bash -l -c
  "<command>"`` string) as well as various other debug-type output. May add
  additional output, or modify pre-existing output.
    
  Where modifying other pieces of output (such as in the above example where it
  modifies the 'running' line to show the shell and any escape characters),
  this setting takes precedence over the others; so if ``running`` is False but
  ``debug`` is True, you will still be shown the 'running' line in its
  debugging form.

In addition to these granular levels, the following act as "aliases" for groups
of the above:

* **output**: Maps to both ``stdout`` and ``stderr``. Useful for when you only
  care to see the 'running' lines and your own print statements (and warnings).

* **everything**: Includes ``warnings``, ``running`` and ``output`` (see
  above.) Thus, when turning off ``everything``, you will only see a bare
  minimum of output, along with your own print statements.

You may toggle any and all of the above levels in a few ways:

* **Direct modification of fabric.state.output**: `fabric.state.output` is a
  dictionary subclass (similar to `fabric.state.env`) whose keys are the above
  levels, and whose value are either True or False. Naturally, a True value
  results in display of that output group, and False hides it.

* **Context managers**: `~fabric.context_managers.hide` and
  `~fabric.context_managers.show` are twin context managers that take one or
  more output level names as strings, and either hide or show them within the
  wrapped block. As with most other context managers, the prior values are
  restored when the block exits.

* **Command-line arguments**: You may pass ``--hide`` and/or ``--show``
  arguments to ``fab``, which behave exactly like the context managers of the
  same names (but are, naturally, globally applied) and take comma-separated
  strings as input.

All levels, save for ``debug``, are on by default.
