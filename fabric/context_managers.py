"""
Context managers for use with the ``with`` statement.

.. note:: When using Python 2.5, you will need to start your fabfile
    with ``from __future__ import with_statement`` in order to make use of
    the ``with`` statement (which is a regular, non ``__future__`` feature of
    Python 2.6+.)
"""

from contextlib import contextmanager, nested

from state import env, output


def _set_output(groups, which):
    # Preserve original values, pull in new given value to use
    previous = {}
    for group in output.expand_aliases(groups):
        previous[group] = output[group]
        output[group] = which
    # Yield control
    yield
    # Restore original values
    output.update(previous)


@contextmanager
def show(*groups):
    """
    Context manager for setting the given output ``groups`` to True.

    ``groups`` must be one or more strings naming the output groups defined in
    `~fabric.state.output`. The given groups will be set to True for the
    duration of the enclosed block, and restored to their previous value
    afterwards.

    For example, to turn on debug output (which is typically off by default)::

        def my_task():
            with show('debug'):
                run('ls /var/www')

    As almost all output groups are displayed by default, `show` is most useful
    for turning on the normally-hidden ``debug`` group, or when you know or
    suspect that code calling your own code is trying to hide output with
    `hide`.
    """
    return _set_output(groups, True)


@contextmanager
def hide(*groups):
    """
    Context manager for setting the given output ``groups`` to False.

    ``groups`` must be one or more strings naming the output groups defined in
    `~fabric.state.output`. The given groups will be set to False for the
    duration of the enclosed block, and restored to their previous value
    afterwards.

    For example, to hide the "[hostname] run:" status lines, as well as
    preventing printout of stdout and stderr, one might use `hide` as follows::

        def my_task():
            with hide('running', 'stdout', 'stderr'):
                run('ls /var/www')
    """
    return _set_output(groups, False)


@contextmanager
def _setenv(**kwargs):
    """
    Context manager temporarily overriding ``env`` with given key/value pairs.

    This context manager is used internally by `settings` and is not intended
    to be used directly.
    """
    previous = {}
    for key, value in kwargs.iteritems():
        previous[key] = env[key]
        env[key] = value
    yield
    env.update(previous)


def settings(*args, **kwargs):
    """
    Nest context managers and/or override ``env`` variables.

    `settings` serves two purposes:

    * Most usefully, it allows temporary overriding/updating of ``env`` with
      any provided keyword arguments, e.g. ``with settings(user='foo'):``.
      Original values, if any, will be restored once the ``with`` block closes.
    * In addition, it will use ``contextlib.nested`` to nest any given
      non-keyword arguments, which should be other context managers, e.g.
      ``with settings(hide('stderr'), show('stdout')):``.

    These behaviors may be specified at the same time if desired. An example
    will hopefully illustrate why this is considered useful::

        def my_task():
            with settings(
                hide('warnings', 'running', 'stdout', 'stderr'),
                warn_only=True
            ):
                if run('ls /etc/lsb-release'):
                    return 'Ubuntu'
                elif run('ls /etc/redhat-release'):
                    return 'RedHat'

    The above task executes a `run` statement, but will warn instead of
    aborting if the ``ls`` fails, and all output -- including the warning
    itself -- is prevented from printing to the user. The end result, in this
    scenario, is a completely silent task that allows the caller to figure out
    what type of system the remote host is, without incurring the handful of
    output that would normally occur.

    Thus, `settings` may be used to set any combination of environment
    variables in tandem with hiding (or showing) specific levels of output, or
    in tandem with any other piece of Fabric functionality implemented as a
    context manager.
    """
    managers = list(args)
    if kwargs:
        managers.append(_setenv(**kwargs))
    return nested(*managers)
