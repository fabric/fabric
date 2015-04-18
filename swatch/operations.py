"""

Functions to be used in fabfiles and other non-core code, such as run()/sudo().
"""

from __future__ import with_statement
from __future__ import absolute_import
from __future__ import print_function

import os
import os.path
import re
import subprocess
from contextlib import contextmanager

from swatch.context_managers import (quiet as quiet_manager, warn_only as
                                     warn_only_manager)

from swatch.state import output
from swatch.utils import (abort, error, handle_prompt_abort, indent, warn,
                          shell_escape)
from swatch.state import env, win32
from swatch.utils import AttributeString
from six.moves import input


# Can't wait till Python versions supporting 'def func(*args, foo=bar)' become
# widespread :(
def require(*keys, **kwargs):
    """
    Check for given keys in the shared environment dict and abort if not found.

    Positional arguments should be strings signifying what env vars should be
    checked for. If any of the given arguments do not exist, swatch will abort
    execution and print the names of the missing keys.

    The optional keyword argument ``used_for`` may be a string, which will be
    printed in the error output to inform users why this requirement is in
    place. ``used_for`` is printed as part of a string similar to::

        "Th(is|ese) variable(s) (are|is) used for %s"

    so format it appropriately.

    The optional keyword argument ``provided_by`` may be a list of functions or
    function names or a single function or function name which the user should
    be able to execute in order to set the key or keys; it will be included in
    the error output if requirements are not met.

    Note: it is assumed that the keyword arguments apply to all given keys as a
    group. If you feel the need to specify more than one ``used_for``, for
    example, you should break your logic into multiple calls to ``require()``.

    .. versionchanged:: 1.1
        Allow iterable ``provided_by`` values instead of just single values.
    """
    # If all keys exist and are non-empty, we're good, so keep going.
    missing_keys = [x for x in keys
                    if x not in env or (x in env and isinstance(
                        env[x], (dict, list, tuple, set)) and not env[x])]
    if not missing_keys:
        return
    # Pluralization
    if len(missing_keys) > 1:
        variable = "variables were"
        used = "These variables are"
    else:
        variable = "variable was"
        used = "This variable is"
    # Regardless of kwargs, print what was missing. (Be graceful if used outside
    # of a command.)
    if 'command' in env:
        prefix = "The command '%s' failed because the " % env.command
    else:
        prefix = "The "
    msg = "%sfollowing required environment %s not defined:\n%s" % (
        prefix, variable, indent(missing_keys)
    )
    # Print used_for if given
    if 'used_for' in kwargs:
        msg += "\n\n%s used for %s" % (used, kwargs['used_for'])
    # And print provided_by if given
    if 'provided_by' in kwargs:
        funcs = kwargs['provided_by']
        # non-iterable is given, treat it as a list of this single item
        if not hasattr(funcs, '__iter__'):
            funcs = [funcs]
        if len(funcs) > 1:
            command = "one of the following commands"
        else:
            command = "the following command"
        to_s = lambda obj: getattr(obj, '__name__', str(obj))
        provided_by = [to_s(obj) for obj in funcs]
        msg += "\n\nTry running %s prior to this one, to fix the problem:\n%s" \
               % (command, indent(provided_by))
    abort(msg)


def prompt(text, key=None, default='', validate=None):
    """
    Prompt user with ``text`` and return the input (like ``raw_input``).

    A single space character will be appended for convenience, but nothing
    else. Thus, you may want to end your prompt text with a question mark or a
    colon, e.g. ``prompt("What hostname?")``.

    If ``key`` is given, the user's input will be stored as ``env.<key>`` in
    addition to being returned by `prompt`. If the key already existed in
    ``env``, its value will be overwritten and a warning printed to the user.

    If ``default`` is given, it is displayed in square brackets and used if the
    user enters nothing (i.e. presses Enter without entering any text).
    ``default`` defaults to the empty string. If non-empty, a space will be
    appended, so that a call such as ``prompt("What hostname?",
    default="foo")`` would result in a prompt of ``What hostname? [foo]`` (with
    a trailing space after the ``[foo]``.)

    The optional keyword argument ``validate`` may be a callable or a string:

    * If a callable, it is called with the user's input, and should return the
      value to be stored on success. On failure, it should raise an exception
      with an exception message, which will be printed to the user.
    * If a string, the value passed to ``validate`` is used as a regular
      expression. It is thus recommended to use raw strings in this case. Note
      that the regular expression, if it is not fully matching (bounded by
      ``^`` and ``$``) it will be made so. In other words, the input must fully
      match the regex.

    Either way, `prompt` will re-prompt until validation passes (or the user
    hits ``Ctrl-C``).

    .. note::
        `~swatch.operations.prompt` honors :ref:`env.abort_on_prompts
        <abort-on-prompts>` and will call `~swatch.utils.abort` instead of
        prompting if that flag is set to ``True``. If you want to block on user
        input regardless, try wrapping with
        `~swatch.context_managers.settings`.

    Examples::

        # Simplest form:
        environment = prompt('Please specify target environment: ')

        # With default, and storing as env.dish:
        prompt('Specify favorite dish: ', 'dish', default='spam & eggs')

        # With validation, i.e. requiring integer input:
        prompt('Please specify process nice level: ', key='nice', validate=int)

        # With validation against a regular expression:
        release = prompt('Please supply a release name',
                validate=r'^\w+-\d+(\.\d+)?$')

        # Prompt regardless of the global abort-on-prompts setting:
        with settings(abort_on_prompts=False):
            prompt('I seriously need an answer on this! ')

    """
    handle_prompt_abort("a user-specified prompt() call")
    # Store previous env value for later display, if necessary
    if key:
        previous_value = env.get(key)
    # Set up default display
    default_str = ""
    if default != '':
        default_str = " [%s] " % str(default).strip()
    else:
        default_str = " "
    # Construct full prompt string
    prompt_str = text.strip() + default_str
    # Loop until we pass validation
    value = None
    while value is None:
        # Get input
        value = eval(input(prompt_str)) or default
        # Handle validation
        if validate:
            # Callable
            if callable(validate):
                # Callable validate() must raise an exception if validation
                # fails.
                try:
                    value = validate(value)
                except Exception as e:
                    # Reset value so we stay in the loop
                    value = None
                    print("Validation failed for the following reason:")
                    print((indent(e.message) + "\n"))
            # String / regex must match and will be empty if validation fails.
            else:
                # Need to transform regex into full-matching one if it's not.
                if not validate.startswith('^'):
                    validate = r'^' + validate
                if not validate.endswith('$'):
                    validate += r'$'
                result = re.findall(validate, value)
                if not result:
                    print((
                        "Regular expression validation failed: '%s' does not match '%s'\n"
                        % (value, validate)))
                    # Reset value so we stay in the loop
                    value = None
    # At this point, value must be valid, so update env if necessary
    if key:
        env[key] = value
    # Print warning if we overwrote some other value
    if key and previous_value is not None and previous_value != value:
        warn(
            "overwrote previous env variable '%s'; used to be '%s', is now '%s'."
            % (key, previous_value, value))
    # And return the value, too, just in case someone finds that useful.
    return value


def _sudo_prefix_argument(argument, value):
    if value is None:
        return ""
    if str(value).isdigit():
        value = "#%s" % value
    return ' %s "%s"' % (argument, value)


def _sudo_prefix(user, group=None):
    """
    Return ``env.sudo_prefix`` with ``user``/``group`` inserted if necessary.
    """
    # Insert env.sudo_prompt into env.sudo_prefix
    prefix = env.sudo_prefix % env
    if user is not None or group is not None:
        return "%s%s%s " % (prefix, _sudo_prefix_argument('-u', user),
                            _sudo_prefix_argument('-g', group))
    return prefix


def _shell_wrap(command, shell_escape, shell=True, sudo_prefix=None):
    """
    Conditionally wrap given command in env.shell (while honoring sudo.)
    """
    # Honor env.shell, while allowing the 'shell' kwarg to override it (at
    # least in terms of turning it off.)
    if shell and not env.use_shell:
        shell = False
    # Sudo plus space, or empty string
    if sudo_prefix is None:
        sudo_prefix = ""
    else:
        sudo_prefix += " "
    # If we're shell wrapping, prefix shell and space. Next, escape the command
    # if requested, and then quote it. Otherwise, empty string.
    if shell:
        shell = env.shell + " "
        if shell_escape:
            command = shell_escape(command)
        command = '"%s"' % command
    else:
        shell = ""
    # Resulting string should now have correct formatting
    return sudo_prefix + shell + command


def _prefix_commands(command, which):
    """
    Prefixes ``command`` with all prefixes found in ``env.command_prefixes``.

    ``env.command_prefixes`` is a list of strings which is modified by the
    `~swatch.context_managers.prefix` context manager.

    This function also handles a special-case prefix, ``cwd``, used by
    `~swatch.context_managers.cd`. The ``which`` kwarg should be a string,
    ``"local"`` or ``"remote"``, which will determine whether ``cwd`` or
    ``lcwd`` is used.
    """
    # Local prefix list (to hold env.command_prefixes + any special cases)
    prefixes = list(env.command_prefixes)
    # Handle current working directory, which gets its own special case due to
    # being a path string that gets grown/shrunk, instead of just a single
    # string or lack thereof.
    # Also place it at the front of the list, in case user is expecting another
    # prefixed command to be "in" the current working directory.
    cwd = env.cwd if which == 'remote' else env.lcwd
    if cwd:
        prefixes.insert(0, 'cd %s' % cwd)
    glue = " && "
    prefix = (glue.join(prefixes) + glue) if prefixes else ""
    return prefix + command


def _prefix_env_vars(command, local=False):
    """
    Prefixes ``command`` with any shell environment vars, e.g. ``PATH=foo ``.

    Currently, this only applies the PATH updating implemented in
    `~swatch.context_managers.path` and environment variables from
    `~swatch.context_managers.shell_env`.

    Will switch to using Windows style 'SET' commands when invoked by
    ``local()`` and on a Windows localhost.
    """
    env_vars = {}

    # path(): local shell env var update, appending/prepending/replacing $PATH
    path = env.path
    if path:
        if env.path_behavior == 'append':
            path = '$PATH:\"%s\"' % path
        elif env.path_behavior == 'prepend':
            path = '\"%s\":$PATH' % path
        elif env.path_behavior == 'replace':
            path = '\"%s\"' % path

        env_vars['PATH'] = path

    # shell_env()
    env_vars.update(env.shell_env)

    if env_vars:
        set_cmd, exp_cmd = '', ''
        if win32 and local:
            set_cmd = 'SET '
        else:
            exp_cmd = 'export '

        exports = ' '.join('%s%s="%s"' % (set_cmd, k, v if k == 'PATH' else
                                          shell_escape(v))
                           for k, v in six.iteritems(env_vars))
        shell_env_str = '%s%s && ' % (exp_cmd, exports)
    else:
        shell_env_str = ''

    return shell_env_str + command


def local(command, capture=False, shell=None):
    """
    Run a command on the local system.

    `local` is simply a convenience wrapper around the use of the builtin
    Python ``subprocess`` module with ``shell=True`` activated. If you need to
    do anything special, consider using the ``subprocess`` module directly.

    ``shell`` is passed directly to `subprocess.Popen
    <http://docs.python.org/library/subprocess.html#subprocess.Popen>`_'s
    ``execute`` argument (which determines the local shell to use.)  As per the
    linked documentation, on Unix the default behavior is to use ``/bin/sh``,
    so this option is useful for setting that value to e.g.  ``/bin/bash``.

    `local` is not currently capable of simultaneously printing and
    capturing output, as `~swatch.operations.run`/`~swatch.operations.sudo`
    do. The ``capture`` kwarg allows you to switch between printing and
    capturing as necessary, and defaults to ``False``.

    When ``capture=False``, the local subprocess' stdout and stderr streams are
    hooked up directly to your terminal, though you may use the global
    :doc:`output controls </usage/output_controls>` ``output.stdout`` and
    ``output.stderr`` to hide one or both if desired. In this mode, the return
    value's stdout/stderr values are always empty.

    When ``capture=True``, you will not see any output from the subprocess in
    your terminal, but the return value will contain the captured
    stdout/stderr.

    In either case, as with `~swatch.operations.run` and
    `~swatch.operations.sudo`, this return value exhibits the ``return_code``,
    ``stderr``, ``failed``, ``succeeded``, ``command`` and ``real_command``
    attributes. See `run` for details.

    `~swatch.operations.local` will honor the `~swatch.context_managers.lcd`
    context manager, allowing you to control its current working directory
    independently of the remote end (which honors
    `~swatch.context_managers.cd`).

    .. versionchanged:: 1.0
        Added the ``succeeded`` and ``stderr`` attributes.
    .. versionchanged:: 1.0
        Now honors the `~swatch.context_managers.lcd` context manager.
    .. versionchanged:: 1.0
        Changed the default value of ``capture`` from ``True`` to ``False``.
    .. versionadded:: 1.9
        The return value attributes ``.command`` and ``.real_command``.
    """
    given_command = command
    # Apply cd(), path() etc
    with_env = _prefix_env_vars(command, local=True)
    wrapped_command = _prefix_commands(with_env, 'local')
    if output.debug:
        print(("[localhost] local: %s" % (wrapped_command)))
    elif output.running:
        print(("[localhost] local: " + given_command))
    # Tie in to global output controls as best we can; our capture argument
    # takes precedence over the output settings.
    dev_null = None
    if capture:
        out_stream = subprocess.PIPE
        err_stream = subprocess.PIPE
    else:
        dev_null = open(os.devnull, 'w+')
        # Non-captured, hidden streams are discarded.
        out_stream = None if output.stdout else dev_null
        err_stream = None if output.stderr else dev_null
    try:
        cmd_arg = wrapped_command if win32 else [wrapped_command]
        p = subprocess.Popen(cmd_arg,
                             shell=True,
                             stdout=out_stream,
                             stderr=err_stream,
                             executable=shell,
                             close_fds=(not win32),
                             universal_newlines=True)
        (stdout, stderr) = p.communicate()
    finally:
        if dev_null is not None:
            dev_null.close()
    # Handle error condition (deal with stdout being None, too)
    out = AttributeString(stdout.strip() if stdout else "")
    err = AttributeString(stderr.strip() if stderr else "")

    # good
    out.command = given_command
    out.real_command = wrapped_command
    out.failed = False
    out.return_code = p.returncode
    out.stderr = err
    if p.returncode not in env.ok_ret_codes:
        out.failed = True
        msg = "local() encountered an error (return code %s) while executing '%s'" % (
            p.returncode, command
        )
        error(message=msg, stdout=out, stderr=err)
    out.succeeded = not out.failed
    # If we were capturing, this will be a string; otherwise it will be None.
    return out
