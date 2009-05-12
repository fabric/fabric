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
    previous = {}
    for group in groups:
        previous[group] = output[group]
        output[group] = which
    yield
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
def setenv(**kwargs):
    """
    Context manager temporarily overriding ``env`` with given key/value pairs.

    This may be used to set any and all environment variables as you see fit. A
    simple example for turning the default abort-on-error behavior into
    warn-on-error could override ``env.warn_only``::

        def my_task():
        with setenv(warn_only=True):
            run('ls /etc/lsb-release')

    As with most other context managers provided with Fabric, `setenv` will
    restore the prior state of ``env`` when it exits.
    """
    previous = {}
    for key, value in kwargs.iteritems():
        previous[key] = env[key]
        env[key] = value
    yield
    env.update(previous)


def settings(*args, **kwargs):
    """
    Meta context manager: args are context managers, kwargs go to `setenv`.

    If any kwargs are given, they are passed directly to an invocation of
    `setenv`; if any args are given, they (along with the invocation of
    `setenv`, if any) are sent to `contextlib.nested`.

    What this means is that `settings` may be used to combine multiple
    Fabric context managers such as `hide` or `show`, with the functionality of
    `setenv` thrown in for convenience's sake (so users do not have to
    explicitly call `setenv` as well, when combining it with other context
    managers.)

    An example will hopefully illustrate why this is considered useful::

        def my_task():
            with settings(
                hide('warnings', 'running', 'stdout', 'stderr'),
                warn_only=True
            ):
                if run('ls /etc/lsb-release'):
                    return 'Ubuntu'
                elif run('ls /etc/redhat-release'):
                    return 'RedHat'

    The above task executes a `run` statement or two, but will warn instead of
    aborting if the `ls` fails, and all output -- including the warning itself
    -- is prevented from printing to the user. The end result, in this
    scenario, is a completely silent task that allows the caller to figure out
    what type of system the remote host is, without incurring the handful of
    output that would normally occur.

    Thus, `settings` may be used to set any combination of environment
    variables in tandem with hiding (or showing) specific levels of output.
    """
    managers = list(args)
    if kwargs:
        managers.append(setenv(**kwargs))
    return nested(*managers)
