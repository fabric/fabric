===============
Managing output
===============

The ``fab`` tool is very verbose by default and prints out almost everything it
can, including the remote end's stderr and stdout streams, the command strings
being executed, and so forth. While this is necessary in many cases in order to
know just what's going on, any nontrivial Fabric task will quickly become
difficult to follow as it runs.


Output levels
=============

To aid in organizing task output, Fabric output is grouped into a number of
non-overlapping levels or groups, each of which may be turned on or off
independently. This provides flexible control over what is displayed to the
user.

.. note::

    All levels, save for ``debug``, are on by default.

Standard output levels
----------------------

The standard, atomic output levels/groups are as follows:

* **status**: Status messages, i.e. noting when Fabric is done running, if
  the user used a keyboard interrupt, or when servers are disconnected from.
  These messages are almost always relevant and rarely verbose.

* **aborts**: Abort messages. Like status messages, these should really only be
  turned off when using Fabric as a library, and possibly not even then. Note
  that even if this output group is turned off, aborts will still occur --
  there just won't be any output about why Fabric aborted!

* **warnings**: Warning messages. These are often turned off when one expects a
  given operation to fail, such as when using ``grep`` to test existence of
  text in a file. If paired with setting ``env.warn_only`` to True, this
  can result in fully silent warnings when remote programs fail. As with
  ``aborts``, this setting does not control actual warning behavior, only
  whether warning messages are printed or hidden.

* **running**: Printouts of commands being executed or files transferred, e.g.
  ``[myserver] run: ls /var/www``. Also controls printing of tasks being run,
  e.g. ``[myserver] Executing task 'foo'``.

* **stdout**: Local, or remote, stdout, i.e. non-error output from commands.

* **stderr**: Local, or remote, stderr, i.e. error-related output from commands.

* **user**: User-generated output, i.e. local output printed by fabfile code
  via use of the `~fabric.utils.fastprint` or `~fabric.utils.puts` functions.

.. versionchanged:: 0.9.2
    Added "Executing task" lines to the ``running`` output level.

.. versionchanged:: 0.9.2
    Added the ``user`` output level.

Debug output
------------

There is a final atomic output level, ``debug``, which behaves slightly
differently from the rest:

* **debug**: Turn on debugging (which is off by default.) Currently, this is
  largely used to view the "full" commands being run; take for example this
  `~fabric.operations.run` call::

      run('ls "/home/username/Folder Name With Spaces/"')

  Normally, the ``running`` line will show exactly what is passed into
  `~fabric.operations.run`, like so::

      [hostname] run: ls "/home/username/Folder Name With Spaces/"

  With ``debug`` on, and assuming you've left :ref:`shell` set to ``True``, you
  will see the literal, full string as passed to the remote server::

      [hostname] run: /bin/bash -l -c "ls \"/home/username/Folder Name With Spaces\""

  Enabling ``debug`` output will also display full Python tracebacks during
  aborts.
  
  .. note::
  
      Where modifying other pieces of output (such as in the above example
      where it modifies the 'running' line to show the shell and any escape
      characters), this setting takes precedence over the others; so if
      ``running`` is False but ``debug`` is True, you will still be shown the
      'running' line in its debugging form.

.. versionchanged:: 1.0
    Debug output now includes full Python tracebacks during aborts.

Output level aliases
--------------------

In addition to the atomic/standalone levels above, Fabric also provides a
couple of convenience aliases which map to multiple other levels. These may be
referenced anywhere the other levels are referenced, and will effectively
toggle all of the levels they are mapped to.

* **output**: Maps to both ``stdout`` and ``stderr``. Useful for when you only
  care to see the 'running' lines and your own print statements (and warnings).

* **everything**: Includes ``warnings``, ``running``, ``user`` and ``output``
  (see above.) Thus, when turning off ``everything``, you will only see a bare
  minimum of output (just ``status`` and ``debug`` if it's on), along with your
  own print statements.


Hiding and/or showing output levels
===================================

You may toggle any of Fabric's output levels in a number of ways; for examples,
please see the API docs linked in each bullet point:

* **Direct modification of fabric.state.output**: `fabric.state.output` is a
  dictionary subclass (similar to :doc:`env <env>`) whose keys are the output
  level names, and whose values are either True (show that particular type of
  output) or False (hide it.)
  
  `fabric.state.output` is the lowest-level implementation of output levels and
  is what Fabric's internals reference when deciding whether or not to print
  their output.

* **Context managers**: `~fabric.context_managers.hide` and
  `~fabric.context_managers.show` are twin context managers that take one or
  more output level names as strings, and either hide or show them within the
  wrapped block. As with Fabric's other context managers, the prior values are
  restored when the block exits.

  .. seealso::

      `~fabric.context_managers.settings`, which can nest calls to
      `~fabric.context_managers.hide` and/or `~fabric.context_managers.show`
      inside itself.

* **Command-line arguments**: You may use the :option:`--hide` and/or
  :option:`--show` arguments to :doc:`fab`, which behave exactly like the
  context managers of the same names (but are, naturally, globally applied) and
  take comma-separated strings as input.
