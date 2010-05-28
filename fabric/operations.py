"""
Functions to be used in fabfiles and other non-core code, such as run()/sudo().
"""

from __future__ import with_statement

from glob import glob
import os
import os.path
import re
import stat
import subprocess
from contextlib import closing

from fabric.network import output_thread, needs_host
from fabric.state import env, connections, output
from fabric.utils import abort, indent, warn


def _handle_failure(message, exception=None):
    """
    Call `abort` or `warn` with the given message.

    The value of ``env.warn_only`` determines which method is called.

    If ``exception`` is given, it is inspected to get a string message, which
    is printed alongside the user-generated ``message``.
    """
    func = env.warn_only and warn or abort
    if exception is not None:
        # Figure out how to get a string out of the exception; EnvironmentError
        # subclasses, for example, "are" integers and .strerror is the string.
        # Others "are" strings themselves. May have to expand this further for
        # other error types.
        if hasattr(exception, 'strerror') and exception.strerror is not None:
            underlying_msg = exception.strerror
        else:
            underlying_msg = exception
        func("%s\n\nUnderlying exception message:\n%s" % (
            message,
            indent(underlying_msg)
        ))
    else:
        func(message)


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
                lmode = mode or os.stat(lpath).st_mode
                if lmode != rattrs.st_mode:
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


@needs_host
def run(command, shell=True, pty=False):
    """
    Run a shell command on a remote host.

    If ``shell`` is True (the default), ``run()`` will execute the given
    command string via a shell interpreter, the value of which may be
    controlled by setting ``env.shell`` (defaulting to something similar to
    ``/bin/bash -l -c "<command>"``.) Any double-quote (``"``) characters in
    ``command`` will be automatically escaped when ``shell`` is True.

    `run` will return the result of the remote program's stdout as a
    single (likely multiline) string. This string will exhibit a ``failed``
    boolean attribute specifying whether the command failed or succeeded, and
    will also include the return code as the ``return_code`` attribute.

    You may pass ``pty=True`` to force allocation of a pseudo tty on
    the remote end. This is not normally required, but some programs may
    complain (or, even more rarely, refuse to run) if a tty is not present.

    Examples::
    
        run("ls /var/www/")
        run("ls /home/myuser", shell=False)
        output = run('ls /var/www/site1')
    
    """
    # Set up new var so original argument can be displayed verbatim later.
    real_command = command
    if shell:
        # Handle cwd munging via 'cd' context manager
        cwd = env.get('cwd', '')
        if cwd:
            # TODO: see if there is any nice way to quote this, given that it
            # ends up inside double quotes down below...
            cwd = 'cd %s && ' % _shell_escape(cwd)
        # Construct final real, full command
        real_command = '%s "%s"' % (env.shell,
            _shell_escape(cwd + real_command))
    if output.debug:
        print("[%s] run: %s" % (env.host_string, real_command))
    elif output.running:
        print("[%s] run: %s" % (env.host_string, command))
    channel = connections[env.host_string]._transport.open_session()
    # Create pty if necessary (using Paramiko default options, which as of
    # 1.7.4 is vt100 $TERM @ 80x24 characters)
    if pty:
        channel.get_pty()
    channel.exec_command(real_command)
    capture = []

    out_thread = output_thread("[%s] out" % env.host_string, channel,
        capture=capture)
    err_thread = output_thread("[%s] err" % env.host_string, channel,
        stderr=True)
    
    # Close when done
    status = channel.recv_exit_status()
    
    # Wait for threads to exit so we aren't left with stale threads
    out_thread.join()
    err_thread.join()

    # Close channel
    channel.close()

    # Assemble output string
    out = _AttributeString("".join(capture).strip())

    # Error handling
    out.failed = False
    if status != 0:
        out.failed = True
        msg = "run() encountered an error (return code %s) while executing '%s'" % (status, command)
        _handle_failure(message=msg)

    # Attach return code to output string so users who have set things to warn
    # only, can inspect the error code.
    out.return_code = status
    return out


@needs_host
def sudo(command, shell=True, user=None, pty=False):
    """
    Run a shell command on a remote host, with superuser privileges.
    
    As with ``run()``, ``sudo()`` executes within a shell command defaulting to
    the value of ``env.shell``, although it goes one step further and wraps the
    command with ``sudo`` as well. Like `run`, this behavior may be disabled by
    specifying ``shell=False``.

    You may specify a ``user`` keyword argument, which is passed to ``sudo``
    and allows you to run as some user other than root (which is the default).
    On most systems, the ``sudo`` program can take a string username or an
    integer userid (uid); ``user`` may likewise be a string or an int.

    Some remote systems may be configured to disallow sudo access unless a
    terminal or pseudoterminal is being used (e.g. when ``Defaults
    requiretty`` exists in ``/etc/sudoers``.) If updating the remote system's
    ``sudoers`` configuration is not possible or desired, you may pass
    ``pty=True`` to `sudo` to force allocation of a pseudo tty on the remote
    end.
       
    `sudo` will return the result of the remote program's stdout as a
    single (likely multiline) string. This string will exhibit a ``failed``
    boolean attribute specifying whether the command failed or succeeded, and
    will also include the return code as the ``return_code`` attribute.

    Examples::
    
        sudo("~/install_script.py")
        sudo("mkdir /var/www/new_docroot", user="www-data")
        sudo("ls /home/jdoe", user=1001)
        result = sudo("ls /tmp/")
    
    """
    # Construct sudo command, with user if necessary
    if user is not None:
        if str(user).isdigit():
            user = "#%s" % user
        sudo_prefix = "sudo -S -p '%%s' -u \"%s\" " % user
    else:
        sudo_prefix = "sudo -S -p '%s' "
    # Put in explicit sudo prompt string (so we know what to look for when
    # detecting prompts)
    sudo_prefix = sudo_prefix % env.sudo_prompt
    # Without using a shell, we just do 'sudo -u blah my_command'
    if (not env.use_shell) or (not shell):
        real_command = "%s %s" % (sudo_prefix, _shell_escape(command))
    # With a shell, we do 'sudo -u blah /bin/bash -l -c "my_command"'
    else:
        # With a shell, we can also honor cwd
        cwd = env.get('cwd', '')
        if cwd:
            # TODO: see if there is any nice way to quote this, given that it
            # ends up inside double quotes down below...
            cwd = 'cd %s && ' % _shell_escape(cwd)
        real_command = '%s %s "%s"' % (sudo_prefix, env.shell,
            _shell_escape(cwd + command))
    if output.debug:
        print("[%s] sudo: %s" % (env.host_string, real_command))
    elif output.running:
        print("[%s] sudo: %s" % (env.host_string, command))
    channel = connections[env.host_string]._transport.open_session()
    # Create pty if necessary (using Paramiko default options, which as of
    # 1.7.4 is vt100 $TERM @ 80x24 characters)
    if pty:
        channel.get_pty()
    # Execute
    channel.exec_command(real_command)
    capture = []

    out_thread = output_thread("[%s] out" % env.host_string, channel, capture=capture)
    err_thread = output_thread("[%s] err" % env.host_string, channel, stderr=True)

    # Close channel when done
    status = channel.recv_exit_status()

    # Wait for threads to exit before returning (otherwise we will occasionally
    # end up returning before the threads have fully wrapped up)
    out_thread.join()
    err_thread.join()

    # Close channel
    channel.close()

    # Assemble stdout string
    out = _AttributeString("".join(capture).strip())

    # Error handling
    out.failed = False
    if status != 0:
        out.failed = True
        msg = "sudo() encountered an error (return code %s) while executing '%s'" % (status, command)
        _handle_failure(message=msg)

    # Attach return code for convenience
    out.return_code = status
    return out


def local(command, capture=True):
    """
    Run a command on the local system.

    `local` is simply a convenience wrapper around the use of the builtin
    Python ``subprocess`` module with ``shell=True`` activated. If you need to
    do anything special, consider using the ``subprocess`` module directly.

    `local` will, by default, capture and return the contents of the command's
    stdout as a string, and will not print anything to the user (the command's
    stderr is captured but discarded.)
    
    .. note::
        This differs from the default behavior of `run` and `sudo` due to the
        different mechanisms involved: it is difficult to simultaneously
        capture and print local commands, so we have to choose one or the
        other. We hope to address this in later releases.

    If you need full interactivity with the command being run (and are willing
    to accept the loss of captured stdout) you may specify ``capture=False`` so
    that the subprocess' stdout and stderr pipes are connected to your terminal
    instead of captured by Fabric.

    When ``capture`` is False, global output controls (``output.stdout`` and
    ``output.stderr`` will be used to determine what is printed and what is
    discarded.
    """
    # Handle cd() context manager
    cwd = env.get('cwd', '')
    if cwd:
        cwd = 'cd %s && ' % _shell_escape(cwd)
    # Construct real command
    real_command = cwd + command
    if output.debug:
        print("[localhost] run: %s" % (real_command))
    elif output.running:
        print("[localhost] run: " + command)
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
    p = subprocess.Popen([real_command], shell=True, stdout=out_stream,
            stderr=err_stream)
    (stdout, stderr) = p.communicate()
    # Handle error condition (deal with stdout being None, too)
    out = _AttributeString(stdout.strip() if stdout else "")
    out.failed = False
    out.return_code = p.returncode
    if p.returncode != 0:
        out.failed = True
        msg = "local() encountered an error (return code %s) while executing '%s'" % (p.returncode, command)
        _handle_failure(message=msg)
    # If we were capturing, this will be a string; otherwise it will be None.
    return out
