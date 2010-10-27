"""
Functions to be used in fabfiles and other non-core code, such as run()/sudo().
"""

from __future__ import with_statement

import os
import os.path
import re
import stat
import subprocess
import sys
import time
from glob import glob
from traceback import format_exc

from contextlib import closing

from fabric.context_managers import settings, char_buffered
from fabric.io import output_loop, input_loop
from fabric.network import needs_host
from fabric.state import env, connections, output, win32, default_channel
from fabric.utils import abort, indent, warn, puts
from fabric.thread_handling import ThreadHandler

# For terminal size logic below
if not win32:
    import fcntl
    import termios
    import struct


def _pty_size():
    """
    Obtain (rows, cols) tuple for sizing a pty on the remote end.

    Defaults to 80x24 (which is also the Paramiko default) but will detect
    local (stdout-based) terminal window size on non-Windows platforms.
    """
    rows, cols = 24, 80
    if not win32 and sys.stdin.isatty():
        # We want two short unsigned integers (rows, cols)
        fmt = 'HH'
        # Create an empty (zeroed) buffer for ioctl to map onto. Yay for C!
        buffer = struct.pack(fmt, 0, 0)
        # Call TIOCGWINSZ to get window size of stdout, returns our filled buffer
        try:
            result = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ,
                buffer)
            # Unpack buffer back into Python data types
            rows, cols = struct.unpack(fmt, result)
        # Deal with e.g. sys.stdout being monkeypatched, such as in testing.
        # Or termios not having a TIOCGWINSZ.
        except AttributeError:
            pass
    return rows, cols


def _handle_failure(message, exception=None):
    """
    Call `abort` or `warn` with the given message.

    The value of ``env.warn_only`` determines which method is called.

    If ``exception`` is given, it is inspected to get a string message, which
    is printed alongside the user-generated ``message``.
    """
    func = env.warn_only and warn or abort
    # If debug printing is on, append a traceback to the message
    if output.debug:
        message += "\n\n" + format_exc()
    # Otherwise, if we were given an exception, append its contents.
    elif exception is not None:
        # Figure out how to get a string out of the exception; EnvironmentError
        # subclasses, for example, "are" integers and .strerror is the string.
        # Others "are" strings themselves. May have to expand this further for
        # other error types.
        if hasattr(exception, 'strerror') and exception.strerror is not None:
            underlying = exception.strerror
        else:
            underlying = exception
        message += "\n\nUnderlying exception message:\n" + indent(underlying)
    return func(message)


def _shell_escape(string):
    """
    Escape double quotes, backticks and dollar signs in given ``string``.

    For example::

        >>> _shell_escape('abc$')
        'abc\\\\$'
        >>> _shell_escape('"')
        '\\\\"'
    """
    for char in ('"', '$', '`'):
        string = string.replace(char, '\%s' % char)
    return string


class _AttributeString(str):
    """
    Simple string subclass to allow arbitrary attribute access.
    """
    @property
    def stdout(self):
        return str(self)


# Can't wait till Python versions supporting 'def func(*args, foo=bar)' become
# widespread :(
def require(*keys, **kwargs):
    """
    Check for given keys in the shared environment dict and abort if not found.

    Positional arguments should be strings signifying what env vars should be
    checked for. If any of the given arguments do not exist, Fabric will abort
    execution and print the names of the missing keys.

    The optional keyword argument ``used_for`` may be a string, which will be
    printed in the error output to inform users why this requirement is in
    place. ``used_for`` is printed as part of a string similar to::
    
        "Th(is|ese) variable(s) (are|is) used for %s"
        
    so format it appropriately.

    The optional keyword argument ``provided_by`` may be a list of functions or
    function names which the user should be able to execute in order to set the
    key or keys; it will be included in the error output if requirements are
    not met.

    Note: it is assumed that the keyword arguments apply to all given keys as a
    group. If you feel the need to specify more than one ``used_for``, for
    example, you should break your logic into multiple calls to ``require()``.
    """
    # If all keys exist, we're good, so keep going.
    missing_keys = filter(lambda x: x not in env, keys)
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
        # Pluralize this too
        if len(funcs) > 1:
            command = "one of the following commands"
        else:
            command = "the following command"
        to_s = lambda obj: getattr(obj, '__name__', str(obj))
        provided_by = [to_s(obj) for obj in funcs]
        msg += "\n\nTry running %s prior to this one, to fix the problem:\n%s"\
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
    
    """
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
        value = raw_input(prompt_str) or default
        # Handle validation
        if validate:
            # Callable
            if callable(validate):
                # Callable validate() must raise an exception if validation
                # fails.
                try:
                    value = validate(value)
                except Exception, e:
                    # Reset value so we stay in the loop
                    value = None
                    print("Validation failed for the following reason:")
                    print(indent(e.message) + "\n")
            # String / regex must match and will be empty if validation fails.
            else:
                # Need to transform regex into full-matching one if it's not.
                if not validate.startswith('^'):
                    validate = r'^' + validate
                if not validate.endswith('$'):
                    validate += r'$'
                result = re.findall(validate, value)
                if not result:
                    print("Regular expression validation failed: '%s' does not match '%s'\n" % (value, validate))
                    # Reset value so we stay in the loop
                    value = None
    # At this point, value must be valid, so update env if necessary
    if key:
        env[key] = value
    # Print warning if we overwrote some other value
    if key and previous_value is not None and previous_value != value:
        warn("overwrote previous env variable '%s'; used to be '%s', is now '%s'." % (
            key, previous_value, value
        ))
    # And return the value, too, just in case someone finds that useful.
    return value


@needs_host
def put(local_path, remote_path, mode=None):
    """
    Upload one or more files to a remote host.
    
    ``local_path`` may be a relative or absolute local file path, and may
    contain shell-style wildcards, as understood by the Python ``glob`` module.
    Tilde expansion (as implemented by ``os.path.expanduser``) is also
    performed.

    ``remote_path`` may also be a relative or absolute location, but applied to
    the remote host. Relative paths are relative to the remote user's home
    directory, but tilde expansion (e.g. ``~/.ssh/``) will also be performed if
    necessary.

    By default, `put` preserves file modes when uploading. However, you can
    also set the mode explicitly by specifying the ``mode`` keyword argument,
    which sets the numeric mode of the remote file. See the ``os.chmod``
    documentation or ``man chmod`` for the format of this argument.
    
    Examples::
    
        put('bin/project.zip', '/tmp/project.zip')
        put('*.py', 'cgi-bin/')
        put('index.html', 'index.html', mode=0755)
    
    """
    ftp = connections[env.host_string].open_sftp()
    with closing(ftp) as ftp:
        # Expand tildes (assumption: default remote cwd is user $HOME)
        remote_path = remote_path.replace('~', ftp.normalize('.'))
        # Get remote mode for directory-vs-file detection
        try:
            rmode = ftp.lstat(remote_path).st_mode
        except:
            # sadly, I see no better way of doing this
            rmode = None
        # Expand local tildes and get globs
        globs = glob(os.path.expanduser(local_path))
        # Deal with bad local_path
        if not globs:
            raise ValueError, "'%s' is not a valid local path or glob." \
                % local_path
    
        # Iterate over all given local files
        for lpath in globs:
            # If remote path is directory, tack on the local filename
            _remote_path = remote_path
            if rmode is not None and stat.S_ISDIR(rmode):
                _remote_path = os.path.join(
                    remote_path,
                    os.path.basename(lpath)
                )
            # Print
            if output.running:
                print("[%s] put: %s -> %s" % (
                    env.host_string, lpath, _remote_path
                ))
            # Try to catch raised exceptions (which is the only way to tell if
            # this operation had problems; there's no return code) during upload
            try:
                # Actually do the upload
                rattrs = ftp.put(lpath, _remote_path)
                # and finally set the file mode
                lmode = (mode or os.stat(lpath).st_mode) & 07777
                rmode = rattrs.st_mode & 07777
                if lmode != rmode:
                    ftp.chmod(_remote_path, lmode)
            except Exception, e:
                msg = "put() encountered an exception while uploading '%s'"
                _handle_failure(message=msg % lpath, exception=e)


@needs_host
def get(remote_path, local_path):
    """
    Download a file from a remote host.
    
    ``remote_path`` should point to a specific file, while ``local_path`` may
    be a directory (in which case the remote filename is preserved) or
    something else (in which case the downloaded file is renamed). Tilde
    expansion is performed on both ends.

    For example, ``get('~/info.txt', '/tmp/')`` will create a new file,
    ``/tmp/info.txt``, because ``/tmp`` is a directory. However, a call such as
    ``get('~/info.txt', '/tmp/my_info.txt')`` would result in a new file named
    ``/tmp/my_info.txt``, as that path didn't exist (and thus wasn't a
    directory.)

    If ``local_path`` names a file that already exists locally, that file
    will be overwritten without complaint.

    Finally, if `get` detects that it will be run on more than one host, it
    will suffix the current host string to the local filename, to avoid
    clobbering when it is run multiple times.

    For example, the following snippet will produce two files on your local
    system, called ``server.log.host1`` and ``server.log.host2`` respectively::
   
        @hosts('host1', 'host2')
        def my_download_task():
            get('/var/log/server.log', 'server.log')

    However, with a single host (e.g. ``@hosts('host1')``), no suffixing is
    performed, leaving you with a single, pristine ``server.log``.
    """
    ftp = connections[env.host_string].open_sftp()
    with closing (ftp) as ftp:
        # Expand tildes (assumption: default remote cwd is user $HOME)
        remote_path = remote_path.replace('~', ftp.normalize('.'))
        local_path = os.path.expanduser(local_path)
        # Detect local directory and append filename if necessary (assuming
        # Unix file separators for now :()
        if os.path.isdir(local_path):
            remote_file = remote_path
            if '/' in remote_file:
                remote_file = remote_file.split('/')[-1]
            local_path = os.path.join(local_path, remote_file)
        # If the current run appears to be scheduled for multiple hosts,
        # append a suffix to the downloaded file to prevent clobbering.
        if len(env.all_hosts) > 1:
            local_path = local_path + '.' + env.host
        # Print
        if output.running:
            print("[%s] download: %s <- %s" % (
                env.host_string, local_path, remote_path
            ))
        # Handle any raised exceptions (no return code to inspect here)
        try:
            ftp.get(remote_path, local_path)
        except Exception, e:
            msg = "get() encountered an exception while downloading '%s'"
            _handle_failure(message=msg % remote_path, exception=e)


def _sudo_prefix(user):
    """
    Return ``env.sudo_prefix`` with ``user`` inserted if necessary.
    """
    # Insert env.sudo_prompt into env.sudo_prefix
    prefix = env.sudo_prefix % env.sudo_prompt
    if user is not None:
        if str(user).isdigit():
            user = "#%s" % user
        return "%s -u \"%s\" " % (prefix, user)
    return prefix


def _shell_wrap(command, shell=True, sudo_prefix=None):
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
    # If we're shell wrapping, prefix shell and space, escape the command and
    # then quote it. Otherwise, empty string.
    if shell:
        shell = env.shell + " "
        command = '"%s"' % _shell_escape(command)
    else:
        shell = ""
    # Resulting string should now have correct formatting
    return sudo_prefix + shell + command


def _prefix_commands(command):
    """
    Prefixes ``command`` with all prefixes found in ``env.command_prefixes``.

    ``env.command_prefixes`` is a list of strings which is modified by the
    `~fabric.context_managers.prefix` context manager.

    This function also handles a special-case prefix, ``cwd``, used by
    `~fabric.context_managers.cd`.
    """
    # Local prefix list (to hold env.command_prefixes + any special cases)
    prefixes = list(env.command_prefixes)
    # Handle current working directory, which gets its own special case due to
    # being a path string that gets grown/shrunk, instead of just a single
    # string or lack thereof.
    # Also place it at the front of the list, in case user is expecting another
    # prefixed command to be "in" the current working directory.
    if env.cwd:
        prefixes.insert(0, 'cd %s' % env.cwd)
    glue = " && "
    prefix = (glue.join(prefixes) + glue) if prefixes else ""
    return prefix + command


def _prefix_env_vars(command):
    """
    Prefixes ``command`` with any shell environment vars, e.g. ``PATH=foo ``.

    Currently, this only applies the PATH updating implemented in
    `~fabric.context_managers.path`.
    """
    # path(): local shell env var update, appending/prepending/replacing $PATH
    path = env.path
    if path:
        if env.path_behavior == 'append':
            path = 'PATH=$PATH:\"%s\" ' % path
        elif env.path_behavior == 'prepend':
            path = 'PATH=\"%s\":$PATH ' % path
        elif env.path_behavior == 'replace':
            path = 'PATH=\"%s\" ' % path
    else:
        path = ''
    return path + command


def _execute(channel, command, pty=True, combine_stderr=True,
    invoke_shell=False):
    """
    Execute ``command`` over ``channel``.

    ``pty`` controls whether a pseudo-terminal is created.

    ``combine_stderr`` controls whether we call ``channel.set_combine_stderr``.

    ``invoke_shell`` controls whether we use ``exec_command`` or
    ``invoke_shell`` (plus a handful of other things, such as always forcing a
    pty.)

    Returns a three-tuple of (``stdout``, ``stderr``, ``status``), where
    ``stdout``/``stderr`` are captured output strings and ``status`` is the
    program's return code, if applicable.
    """
    with char_buffered(sys.stdin):
        # Combine stdout and stderr to get around oddball mixing issues
        if combine_stderr or env.combine_stderr:
            channel.set_combine_stderr(True)

        # Assume pty use, and allow overriding of this either via kwarg or env
        # var.  (invoke_shell always wants a pty no matter what.)
        using_pty = True
        if not invoke_shell and (not pty or not env.always_use_pty):
            using_pty = False
        # Request pty with size params (default to 80x24, obtain real
        # parameters if on POSIX platform)
        if using_pty:
            rows, cols = _pty_size()
            channel.get_pty(width=cols, height=rows)

        # Kick off remote command
        if invoke_shell:
            channel.invoke_shell()
            if command:
                channel.sendall(command + "\n")
        else:
            channel.exec_command(command)

        # Init stdout, stderr capturing. Must use lists instead of strings as
        # strings are immutable and we're using these as pass-by-reference
        stdout, stderr = [], []
        if invoke_shell:
            stdout = stderr = None

        workers = (
            ThreadHandler('out', output_loop, channel, "recv", stdout),
            ThreadHandler('err', output_loop, channel, "recv_stderr", stderr),
            ThreadHandler('in', input_loop, channel, using_pty)
        )

        while True:
            if channel.exit_status_ready():
                break
            else:
                for worker in workers:
                    e = worker.exception
                    if e:
                        raise e[0], e[1], e[2]

        # Obtain exit code of remote program now that we're done.
        status = channel.recv_exit_status()

        # Wait for threads to exit so we aren't left with stale threads
        for worker in workers:
            worker.thread.join()

        # Close channel
        channel.close()

        # Update stdout/stderr with captured values if applicable
        if not invoke_shell:
            stdout = ''.join(stdout).strip()
            stderr = ''.join(stderr).strip()

        # Tie off "loose" output by printing a newline. Helps to ensure any
        # following print()s aren't on the same line as a trailing line prefix
        # or similar. However, don't add an extra newline if we've already
        # ended up with one, as that adds a entire blank line instead.
        if output.running \
            and (output.stdout and stdout and not stdout.endswith("\n")) \
            or (output.stderr and stderr and not stderr.endswith("\n")):
            print("")

        return stdout, stderr, status


@needs_host
def open_shell(command=None):
    """
    Invoke a fully interactive shell on the remote end.

    If ``command`` is given, it will be sent down the pipe before handing
    control over to the invoking user.

    This function is most useful for when you need to interact with a heavily
    shell-based command or series of commands, such as when debugging or when
    fully interactive recovery is required upon remote program failure.

    It should be considered an easy way to work an interactive shell session
    into the middle of a Fabric script and is *not* a drop-in replacement for
    `~fabric.operations.run`, which is also capable of interacting with the
    remote end (albeit only while its given command is executing) and has much
    stronger programmatic abilities such as error handling and stdout/stderr
    capture.

    Specifically, `~fabric.operations.open_shell` provides a better interactive
    experience than `~fabric.operations.run`, but use of a full remote shell
    prevents Fabric from determining whether programs run within the shell have
    failed, and pollutes the stdout/stderr stream with shell output such as
    login banners, prompts and echoed stdin.

    Thus, this function does not have a return value and will not trigger
    Fabric's failure handling if any remote programs result in errors.

    .. versionadded:: 1.0
    """
    _execute(default_channel(), command, True, True, True)


def _run_command(command, shell=True, pty=True, combine_stderr=True,
    sudo=False, user=None):
    """
    Underpinnings of `run` and `sudo`. See their docstrings for more info.
    """
    # Set up new var so original argument can be displayed verbatim later.
    given_command = command
    # Handle context manager modifications, and shell wrapping
    wrapped_command = _shell_wrap(
        _prefix_commands(_prefix_env_vars(command)),
        shell,
        _sudo_prefix(user) if sudo else None
    )
    # Execute info line
    which = 'sudo' if sudo else 'run'
    if output.debug:
        print("[%s] %s: %s" % (env.host_string, which, wrapped_command))
    elif output.running:
        print("[%s] %s: %s" % (env.host_string, which, given_command))

    # Actual execution, stdin/stdout/stderr handling, and termination
    stdout, stderr, status = _execute(default_channel(), wrapped_command, pty,
        combine_stderr)

    # Assemble output string
    out = _AttributeString(stdout)
    err = _AttributeString(stderr)

    # Error handling
    out.failed = False
    if status != 0:
        out.failed = True
        msg = "%s() encountered an error (return code %s) while executing '%s'" % (which, status, command)
        _handle_failure(message=msg)

    # Attach return code to output string so users who have set things to
    # warn only, can inspect the error code.
    out.return_code = status

    # Convenience mirror of .failed
    out.succeeded = not out.failed

    # Attach stderr for anyone interested in that.
    out.stderr = err

    return out


@needs_host
def run(command, shell=True, pty=True, combine_stderr=True):
    """
    Run a shell command on a remote host.

    If ``shell`` is True (the default), `run` will execute the given command
    string via a shell interpreter, the value of which may be controlled by
    setting ``env.shell`` (defaulting to something similar to ``/bin/bash -l -c
    "<command>"``.) Any double-quote (``"``) or dollar-sign (``$``) characters
    in ``command`` will be automatically escaped when ``shell`` is True.

    `run` will return the result of the remote program's stdout as a single
    (likely multiline) string. This string will exhibit ``failed`` and
    ``succeeded`` boolean attributes specifying whether the command failed or
    succeeded, and will also include the return code as the ``return_code``
    attribute.

    Any text entered in your local terminal will be forwarded to the remote
    program as it runs, thus allowing you to interact with password or other
    prompts naturally. For more on how this works, see
    :doc:`/usage/interactivity`.

    You may pass ``pty=False`` to forego creation of a pseudo-terminal on the
    remote end in case the presence of one causes problems for the command in
    question. However, this will force Fabric itself to echo any  and all input
    you type while the command is running, including sensitive passwords. (With
    ``pty=True``, the remote pseudo-terminal will echo for you, and will
    intelligently handle password-style prompts.) See :ref:`pseudottys` for
    details.

    Similarly, if you need to programmatically examine the stderr stream of the
    remote program (exhibited as the ``stderr`` attribute on this function's
    return value), you may set ``combine_stderr=False``. Doing so has a high
    chance of causing garbled output to appear on your terminal (though the
    resulting strings returned by `~fabric.operations.run` will be properly
    separated). For more info, please read :ref:`combine_streams`.

    Examples::
    
        run("ls /var/www/")
        run("ls /home/myuser", shell=False)
        output = run('ls /var/www/site1')
    
    .. versionadded:: 1.0
        The ``succeeded`` and ``stderr`` return value attributes, the
        ``combine_stderr`` kwarg, and interactive behavior.

    .. versionchanged:: 1.0
        The default value of ``pty`` is now ``True``.
    """
    return _run_command(command, shell, pty, combine_stderr)


@needs_host
def sudo(command, shell=True, pty=True, combine_stderr=True, user=None):
    """
    Run a shell command on a remote host, with superuser privileges.

    `sudo` is identical in every way to `run`, except that it will always wrap
    the given ``command`` in a call to the ``sudo`` program to provide
    superuser privileges.

    `sudo` accepts an additional ``user`` argument, which is passed to ``sudo``
    and allows you to run as some user other than root.  On most systems, the
    ``sudo`` program can take a string username or an integer userid (uid);
    ``user`` may likewise be a string or an int.

    Examples::
    
        sudo("~/install_script.py")
        sudo("mkdir /var/www/new_docroot", user="www-data")
        sudo("ls /home/jdoe", user=1001)
        result = sudo("ls /tmp/")
    
    .. versionchanged:: 1.0
        See the changed and added notes for `~fabric.operations.run`.
    """
    return _run_command(command, shell, pty, combine_stderr, sudo=True,
        user=user)


def local(command, capture=True):
    """
    Run a command on the local system.

    `local` is simply a convenience wrapper around the use of the builtin
    Python ``subprocess`` module with ``shell=True`` activated. If you need to
    do anything special, consider using the ``subprocess`` module directly.

    `local` will, by default, capture and return the contents of the command's
    stdout as a string, and will not print anything to the user. As with `run`
    and `sudo`, this return value exhibits the ``return_code``, ``stderr``,
    ``failed`` and ``succeeded`` attributes. See `run` for details.
    
    .. note::
        `local`'s capturing behavior differs from the default behavior of `run`
        and `sudo` due to the different mechanisms involved: it is difficult to
        simultaneously capture and print local commands, so we have to choose
        one or the other. We hope to address this in later releases.

    If you need full interactivity with the command being run (and are willing
    to accept the loss of captured stdout) you may specify ``capture=False`` so
    that the subprocess' stdout and stderr pipes are connected to your terminal
    instead of captured by Fabric.

    When ``capture`` is False, global output controls (``output.stdout`` and
    ``output.stderr`` will be used to determine what is printed and what is
    discarded.

    .. versionchanged:: 1.0
        Added the ``succeeded`` attribute.
    .. versionchanged:: 1.0
        Now honors the `~fabric.context_managers.cd` context manager.
    .. versionchanged:: 1.0
        Added the ``stderr`` attribute.
    """
    given_command = command
    # Apply cd(), path() etc
    wrapped_command = _prefix_commands(_prefix_env_vars(command))
    if output.debug:
        print("[localhost] local: %s" % (wrapped_command))
    elif output.running:
        print("[localhost] local: " + given_command)
    # By default, capture both stdout and stderr
    PIPE = subprocess.PIPE
    out_stream = PIPE
    err_stream = PIPE
    # Tie in to global output controls as best we can; our capture argument
    # takes precedence over the output settings.
    if not capture:
        if output.stdout:
            out_stream = None
        if output.stderr:
            err_stream = None
    p = subprocess.Popen([wrapped_command], shell=True, stdout=out_stream,
            stderr=err_stream)
    (stdout, stderr) = p.communicate()
    # Handle error condition (deal with stdout being None, too)
    out = _AttributeString(stdout.strip() if stdout else "")
    err = _AttributeString(stderr.strip() if stderr else "")
    out.failed = False
    out.return_code = p.returncode
    out.stderr = err
    if p.returncode != 0:
        out.failed = True
        msg = "local() encountered an error (return code %s) while executing '%s'" % (p.returncode, command)
        _handle_failure(message=msg)
    out.succeeded = not out.failed
    # If we were capturing, this will be a string; otherwise it will be None.
    return out


@needs_host
def reboot(wait):
    """
    Reboot the remote system, disconnect, and wait for ``wait`` seconds.

    After calling this operation, further execution of `run` or `sudo` will
    result in a normal reconnection to the server, including any password
    prompts.

    .. versionadded:: 0.9.2
    """
    sudo('reboot')
    client = connections[env.host_string]
    client.close()
    del connections[env.host_string]
    if output.running:
        puts("Waiting for reboot: ", flush=True, end='')
        per_tick = 5
        for second in range(int(wait / per_tick)):
            puts(".", show_prefix=False, flush=True, end='')
            time.sleep(per_tick)
        puts("done.\n", show_prefix=False, flush=True)
