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
from contextlib import closing

from fabric.context_managers import settings, char_buffered, hide
from fabric.io import output_loop, input_loop
from fabric.network import needs_host, ssh, ssh_config
from fabric.sftp import SFTP
from fabric.state import env, connections, output, win32, default_channel
from fabric.thread_handling import ThreadHandler
from fabric.utils import abort, indent, warn, puts, handle_prompt_abort, error, _pty_size

# For terminal size logic below
if not win32:
    import fcntl
    import termios
    import struct


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


class _AttributeList(list):
    """
    Like _AttributeString, but for lists.
    """
    pass


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
    function names or a single function or function name which the user should
    be able to execute in order to set the key or keys; it will be included in
    the error output if requirements are not met.

    Note: it is assumed that the keyword arguments apply to all given keys as a
    group. If you feel the need to specify more than one ``used_for``, for
    example, you should break your logic into multiple calls to ``require()``.

    .. versionchanged:: 1.1
        Allow iterable ``provided_by`` values instead of just single values.
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
        # non-iterable is given, treat it as a list of this single item
        if not hasattr(funcs, '__iter__'):
            funcs = [funcs]
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

    .. note::
        `~fabric.operations.prompt` honors :ref:`env.abort_on_prompts
        <abort-on-prompts>` and will call `~fabric.utils.abort` instead of
        prompting if that flag is set to ``True``. If you want to block on user
        input regardless, try wrapping with
        `~fabric.context_managers.settings`.

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
def put(local_path=None, remote_path=None, use_sudo=False,
    mirror_local_mode=False, mode=None):
    """
    Upload one or more files to a remote host.

    `~fabric.operations.put` returns an iterable containing the absolute file
    paths of all remote files uploaded. This iterable also exhibits a
    ``.failed`` attribute containing any local file paths which failed to
    upload (and may thus be used as a boolean test.) You may also check
    ``.succeeded`` which is equivalent to ``not .failed``.

    ``local_path`` may be a relative or absolute local file or directory path,
    and may contain shell-style wildcards, as understood by the Python ``glob``
    module.  Tilde expansion (as implemented by ``os.path.expanduser``) is also
    performed.

    ``local_path`` may alternately be a file-like object, such as the result of
    ``open('path')`` or a ``StringIO`` instance.

    .. note::
        In this case, `~fabric.operations.put` will attempt to read the entire
        contents of the file-like object by rewinding it using ``seek`` (and
        will use ``tell`` afterwards to preserve the previous file position).

    .. note::
        Use of a file-like object in `~fabric.operations.put`'s ``local_path``
        argument will cause a temporary file to be utilized due to limitations
        in our SSH layer's API.

    ``remote_path`` may also be a relative or absolute location, but applied to
    the remote host. Relative paths are relative to the remote user's home
    directory, but tilde expansion (e.g. ``~/.ssh/``) will also be performed if
    necessary.

    An empty string, in either path argument, will be replaced by the
    appropriate end's current working directory.

    While the SFTP protocol (which `put` uses) has no direct ability to upload
    files to locations not owned by the connecting user, you may specify
    ``use_sudo=True`` to work around this. When set, this setting causes `put`
    to upload the local files to a temporary location on the remote end, and
    then use `sudo` to move them to ``remote_path``.

    In some use cases, it is desirable to force a newly uploaded file to match
    the mode of its local counterpart (such as when uploading executable
    scripts). To do this, specify ``mirror_local_mode=True``.

    Alternately, you may use the ``mode`` kwarg to specify an exact mode, in
    the same vein as ``os.chmod`` or the Unix ``chmod`` command.

    `~fabric.operations.put` will honor `~fabric.context_managers.cd`, so
    relative values in ``remote_path`` will be prepended by the current remote
    working directory, if applicable. Thus, for example, the below snippet
    would attempt to upload to ``/tmp/files/test.txt`` instead of
    ``~/files/test.txt``::

        with cd('/tmp'):
            put('/path/to/local/test.txt', 'files')

    Use of `~fabric.context_managers.lcd` will affect ``local_path`` in the
    same manner.

    Examples::

        put('bin/project.zip', '/tmp/project.zip')
        put('*.py', 'cgi-bin/')
        put('index.html', 'index.html', mode=0755)

    .. versionchanged:: 1.0
        Now honors the remote working directory as manipulated by
        `~fabric.context_managers.cd`, and the local working directory as
        manipulated by `~fabric.context_managers.lcd`.
    .. versionchanged:: 1.0
        Now allows file-like objects in the ``local_path`` argument.
    .. versionchanged:: 1.0
        Directories may be specified in the ``local_path`` argument and will
        trigger recursive uploads.
    .. versionchanged:: 1.0
        Return value is now an iterable of uploaded remote file paths which
        also exhibits the ``.failed`` and ``.succeeded`` attributes.
    """
    # Handle empty local path
    local_path = local_path or os.getcwd()

    # Test whether local_path is a path or a file-like object
    local_is_path = not (hasattr(local_path, 'read') \
        and callable(local_path.read))

    ftp = SFTP(env.host_string)

    with closing(ftp) as ftp:
        home = ftp.normalize('.')

        # Empty remote path implies cwd
        remote_path = remote_path or home

        # Expand tildes
        if remote_path.startswith('~'):
            remote_path = remote_path.replace('~', home, 1)

        # Honor cd() (assumes Unix style file paths on remote end)
        if not os.path.isabs(remote_path) and env.get('cwd'):
            remote_path = env.cwd.rstrip('/') + '/' + remote_path

        if local_is_path:
            # Expand local paths
            local_path = os.path.expanduser(local_path)
            # Honor lcd() where it makes sense
            if not os.path.isabs(local_path) and env.lcwd:
                local_path = os.path.join(env.lcwd, local_path)

            # Glob local path
            names = glob(local_path)
        else:
            names = [local_path]

        # Make sure local arg exists
        if local_is_path and not names:
            err = "'%s' is not a valid local path or glob." % local_path
            raise ValueError(err)

        # Sanity check and wierd cases
        if ftp.exists(remote_path):
            if local_is_path and len(names) != 1 and not ftp.isdir(remote_path):
                raise ValueError("'%s' is not a directory" % remote_path)

        # Iterate over all given local files
        remote_paths = []
        failed_local_paths = []
        for lpath in names:
            try:
                if local_is_path and os.path.isdir(lpath):
                    p = ftp.put_dir(lpath, remote_path, use_sudo,
                        mirror_local_mode, mode)
                    remote_paths.extend(p)
                else:
                    p = ftp.put(lpath, remote_path, use_sudo, mirror_local_mode,
                        mode, local_is_path)
                    remote_paths.append(p)
            except Exception, e:
                msg = "put() encountered an exception while uploading '%s'"
                failure = lpath if local_is_path else "<StringIO>"
                failed_local_paths.append(failure)
                error(message=msg % lpath, exception=e)

        ret = _AttributeList(remote_paths)
        ret.failed = failed_local_paths
        ret.succeeded = not ret.failed
        return ret


@needs_host
def get(remote_path, local_path=None):
    """
    Download one or more files from a remote host.

    `~fabric.operations.get` returns an iterable containing the absolute paths
    to all local files downloaded, which will be empty if ``local_path`` was a
    StringIO object (see below for more on using StringIO). This object will
    also exhibit a ``.failed`` attribute containing any remote file paths which
    failed to download, and a ``.succeeded`` attribute equivalent to ``not
    .failed``.

    ``remote_path`` is the remote file or directory path to download, which may
    contain shell glob syntax, e.g. ``"/var/log/apache2/*.log"``, and will have
    tildes replaced by the remote home directory. Relative paths will be
    considered relative to the remote user's home directory, or the current
    remote working directory as manipulated by `~fabric.context_managers.cd`.
    If the remote path points to a directory, that directory will be downloaded
    recursively.

    ``local_path`` is the local file path where the downloaded file or files
    will be stored. If relative, it will honor the local current working
    directory as manipulated by `~fabric.context_managers.lcd`. It may be
    interpolated, using standard Python dict-based interpolation, with the
    following variables:

    * ``host``: The value of ``env.host_string``, eg ``myhostname`` or
      ``user@myhostname-222`` (the colon between hostname and port is turned
      into a dash to maximize filesystem compatibility)
    * ``dirname``: The directory part of the remote file path, e.g. the
      ``src/projectname`` in ``src/projectname/utils.py``.
    * ``basename``: The filename part of the remote file path, e.g. the
      ``utils.py`` in ``src/projectname/utils.py``
    * ``path``: The full remote path, e.g. ``src/projectname/utils.py``.

    .. note::
        When ``remote_path`` is an absolute directory path, only the inner
        directories will be recreated locally and passed into the above
        variables. So for example, ``get('/var/log', '%(path)s')`` would start
        writing out files like ``apache2/access.log``,
        ``postgresql/8.4/postgresql.log``, etc, in the local working directory.
        It would **not** write out e.g.  ``var/log/apache2/access.log``.

        Additionally, when downloading a single file, ``%(dirname)s`` and
        ``%(path)s`` do not make as much sense and will be empty and equivalent
        to ``%(basename)s``, respectively. Thus a call like
        ``get('/var/log/apache2/access.log', '%(path)s')`` will save a local
        file named ``access.log``, not ``var/log/apache2/access.log``.

        This behavior is intended to be consistent with the command-line
        ``scp`` program.

    If left blank, ``local_path`` defaults to ``"%(host)s/%(path)s"`` in order
    to be safe for multi-host invocations.

    .. warning::
        If your ``local_path`` argument does not contain ``%(host)s`` and your
        `~fabric.operations.get` call runs against multiple hosts, your local
        files will be overwritten on each successive run!

    If ``local_path`` does not make use of the above variables (i.e. if it is a
    simple, explicit file path) it will act similar to ``scp`` or ``cp``,
    overwriting pre-existing files if necessary, downloading into a directory
    if given (e.g. ``get('/path/to/remote_file.txt', 'local_directory')`` will
    create ``local_directory/remote_file.txt``) and so forth.

    ``local_path`` may alternately be a file-like object, such as the result of
    ``open('path', 'w')`` or a ``StringIO`` instance.

    .. note::
        Attempting to `get` a directory into a file-like object is not valid
        and will result in an error.

    .. note::
        This function will use ``seek`` and ``tell`` to overwrite the entire
        contents of the file-like object, in order to be consistent with the
        behavior of `~fabric.operations.put` (which also considers the entire
        file). However, unlike `~fabric.operations.put`, the file pointer will
        not be restored to its previous location, as that doesn't make as much
        sense here and/or may not even be possible.

    .. note::
        Due to how our SSH layer works, a temporary file will still be written
        to your hard disk even if you specify a file-like object such as a
        StringIO for the ``local_path`` argument. Cleanup is performed,
        however -- we just note this for users expecting straight-to-memory
        transfers. (We hope to patch our SSH layer in the future to enable true
        straight-to-memory downloads.)

    .. versionchanged:: 1.0
        Now honors the remote working directory as manipulated by
        `~fabric.context_managers.cd`, and the local working directory as
        manipulated by `~fabric.context_managers.lcd`.
    .. versionchanged:: 1.0
        Now allows file-like objects in the ``local_path`` argument.
    .. versionchanged:: 1.0
        ``local_path`` may now contain interpolated path- and host-related
        variables.
    .. versionchanged:: 1.0
        Directories may be specified in the ``remote_path`` argument and will
        trigger recursive downloads.
    .. versionchanged:: 1.0
        Return value is now an iterable of downloaded local file paths, which
        also exhibits the ``.failed`` and ``.succeeded`` attributes.
    """
    # Handle empty local path / default kwarg value
    local_path = local_path or "%(host)s/%(path)s"

    # Test whether local_path is a path or a file-like object
    local_is_path = not (hasattr(local_path, 'write') \
        and callable(local_path.write))

    # Honor lcd() where it makes sense
    if local_is_path and not os.path.isabs(local_path) and env.lcwd:
        local_path = os.path.join(env.lcwd, local_path)

    ftp = SFTP(env.host_string)

    with closing(ftp) as ftp:
        home = ftp.normalize('.')
        # Expand home directory markers (tildes, etc)
        if remote_path.startswith('~'):
            remote_path = remote_path.replace('~', home, 1)
        if local_is_path:
            local_path = os.path.expanduser(local_path)

        # Honor cd() (assumes Unix style file paths on remote end)
        if not os.path.isabs(remote_path):
            # Honor cwd if it's set (usually by with cd():)
            if env.get('cwd'):
                remote_path = env.cwd.rstrip('/') + '/' + remote_path
            # Otherwise, be relative to remote home directory (SFTP server's
            # '.')
            else:
                remote_path = os.path.join(home, remote_path)

        # Track final local destination files so we can return a list
        local_files = []
        failed_remote_files = []

        try:
            # Glob remote path
            names = ftp.glob(remote_path)

            # Handle invalid local-file-object situations
            if not local_is_path:
                if len(names) > 1 or ftp.isdir(names[0]):
                    error("[%s] %s is a glob or directory, but local_path is a file object!" % (env.host_string, remote_path))

            for remote_path in names:
                if ftp.isdir(remote_path):
                    result = ftp.get_dir(remote_path, local_path)
                    local_files.extend(result)
                else:
                    # Result here can be file contents (if not local_is_path)
                    # or final resultant file path (if local_is_path)
                    result = ftp.get(remote_path, local_path, local_is_path,
                        os.path.basename(remote_path))
                    if not local_is_path:
                        # Overwrite entire contents of local_path
                        local_path.seek(0)
                        local_path.write(result)
                    else:
                        local_files.append(result)

        except Exception, e:
            failed_remote_files.append(remote_path)
            msg = "get() encountered an exception while downloading '%s'"
            error(message=msg % remote_path, exception=e)

        ret = _AttributeList(local_files if local_is_path else [])
        ret.failed = failed_remote_files
        ret.succeeded = not ret.failed
        return ret


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


def _prefix_commands(command, which):
    """
    Prefixes ``command`` with all prefixes found in ``env.command_prefixes``.

    ``env.command_prefixes`` is a list of strings which is modified by the
    `~fabric.context_managers.prefix` context manager.

    This function also handles a special-case prefix, ``cwd``, used by
    `~fabric.context_managers.cd`. The ``which`` kwarg should be a string,
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


def _execute(channel, command, pty=True, combine_stderr=None,
    invoke_shell=False):
    """
    Execute ``command`` over ``channel``.

    ``pty`` controls whether a pseudo-terminal is created.

    ``combine_stderr`` controls whether we call ``channel.set_combine_stderr``.
    By default, the global setting for this behavior (:ref:`env.combine_stderr
    <combine-stderr>`) is consulted, but you may specify ``True`` or ``False``
    here to override it.

    ``invoke_shell`` controls whether we use ``exec_command`` or
    ``invoke_shell`` (plus a handful of other things, such as always forcing a
    pty.)

    Returns a three-tuple of (``stdout``, ``stderr``, ``status``), where
    ``stdout``/``stderr`` are captured output strings and ``status`` is the
    program's return code, if applicable.
    """
    with char_buffered(sys.stdin):
        # Combine stdout and stderr to get around oddball mixing issues
        if combine_stderr is None:
            combine_stderr = env.combine_stderr
        channel.set_combine_stderr(combine_stderr)

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

        # Use SSH agent forwarding from 'ssh' if enabled by user
        config_agent = ssh_config().get('forwardagent', 'no').lower() == 'yes'
        if env.forward_agent or config_agent:
            forward = ssh.agent.AgentClientProxy(channel)

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
            time.sleep(ssh.io_sleep)

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
        _prefix_commands(_prefix_env_vars(command), 'remote'),
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
        msg = "%s() received nonzero return code %s while executing" % (
            which, status
        )
        if env.warn_only:
            msg += " '%s'!" % given_command
        else:
            msg += "!\n\nRequested: %s\nExecuted: %s" % (
                given_command, wrapped_command
            )
        error(message=msg, stdout=out, stderr=err)

    # Attach return code to output string so users who have set things to
    # warn only, can inspect the error code.
    out.return_code = status

    # Convenience mirror of .failed
    out.succeeded = not out.failed

    # Attach stderr for anyone interested in that.
    out.stderr = err

    return out


@needs_host
def run(command, shell=True, pty=True, combine_stderr=None):
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

    .. versionchanged:: 1.0.2
        The default value of ``combine_stderr`` is now ``None`` instead of
        ``True``. However, the default *behavior* is unchanged, as the global
        setting is still ``True``.
    """
    return _run_command(command, shell, pty, combine_stderr)


@needs_host
def sudo(command, shell=True, pty=True, combine_stderr=None, user=None):
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


def local(command, capture=False):
    """
    Run a command on the local system.

    `local` is simply a convenience wrapper around the use of the builtin
    Python ``subprocess`` module with ``shell=True`` activated. If you need to
    do anything special, consider using the ``subprocess`` module directly.

    `local` is not currently capable of simultaneously printing and
    capturing output, as `~fabric.operations.run`/`~fabric.operations.sudo`
    do. The ``capture`` kwarg allows you to switch between printing and
    capturing as necessary, and defaults to ``False``.

    When ``capture=False``, the local subprocess' stdout and stderr streams are
    hooked up directly to your terminal, though you may use the global
    :doc:`output controls </usage/output_controls>` ``output.stdout`` and
    ``output.stderr`` to hide one or both if desired. In this mode,
    `~fabric.operations.local` returns None.

    When ``capture=True``, this function will return the contents of the
    command's stdout as a string-like object; as with `~fabric.operations.run`
    and `~fabric.operations.sudo`, this return value exhibits the
    ``return_code``, ``stderr``, ``failed`` and ``succeeded`` attributes. See
    `run` for details.

    `~fabric.operations.local` will honor the `~fabric.context_managers.lcd`
    context manager, allowing you to control its current working directory
    independently of the remote end (which honors
    `~fabric.context_managers.cd`).

    .. versionchanged:: 1.0
        Added the ``succeeded`` and ``stderr`` attributes.
    .. versionchanged:: 1.0
        Now honors the `~fabric.context_managers.lcd` context manager.
    .. versionchanged:: 1.0
        Changed the default value of ``capture`` from ``True`` to ``False``.
    """
    given_command = command
    # Apply cd(), path() etc
    wrapped_command = _prefix_commands(_prefix_env_vars(command), 'local')
    if output.debug:
        print("[localhost] local: %s" % (wrapped_command))
    elif output.running:
        print("[localhost] local: " + given_command)
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
        p = subprocess.Popen(cmd_arg, shell=True, stdout=out_stream,
            stderr=err_stream)
        (stdout, stderr) = p.communicate()
    finally:
        if dev_null is not None:
            dev_null.close()
    # Handle error condition (deal with stdout being None, too)
    out = _AttributeString(stdout.strip() if stdout else "")
    err = _AttributeString(stderr.strip() if stderr else "")
    out.failed = False
    out.return_code = p.returncode
    out.stderr = err
    if p.returncode != 0:
        out.failed = True
        msg = "local() encountered an error (return code %s) while executing '%s'" % (p.returncode, command)
        error(message=msg)
    out.succeeded = not out.failed
    # If we were capturing, this will be a string; otherwise it will be None.
    return out


@needs_host
def reboot(wait=120):
    """
    Reboot the remote system.

    Will temporarily tweak Fabric's reconnection settings (:ref:`timeout` and
    :ref:`connection-attempts`) to ensure that reconnection does not give up
    for at least ``wait`` seconds.

    .. note::
        As of Fabric 1.4, the ability to reconnect partway through a session no
        longer requires use of internal APIs.  While we are not officially
        deprecating this function, adding more features to it will not be a
        priority.

        Users who want greater control
        are encouraged to check out this function's (6 lines long, well
        commented) source code and write their own adaptation using different
        timeout/attempt values or additional logic.

    .. versionadded:: 0.9.2
    .. versionchanged:: 1.4
        Changed the ``wait`` kwarg to be optional, and refactored to leverage
        the new reconnection functionality; it may not actually have to wait
        for ``wait`` seconds before reconnecting.
    """
    # Shorter timeout for a more granular cycle than the default.
    timeout = 5
    # Use 'wait' as max total wait time
    attempts = int(round(wait / float(timeout)))
    # Don't bleed settings, since this is supposed to be self-contained.
    # User adaptations will probably want to drop the "with settings()" and
    # just have globally set timeout/attempts values.
    with settings(
        hide('running'),
        timeout=timeout,
        connection_attempts=attempts
    ):
        sudo('reboot')
        # Try to make sure we don't slip in before pre-reboot lockdown
        time.sleep(5)
        # This is actually an internal-ish API call, but users can simply drop
        # it in real fabfile use -- the next run/sudo/put/get/etc call will
        # automatically trigger a reconnect.
        # We use it here to force the reconnect while this function is still in
        # control and has the above timeout settings enabled.
        connections.connect(env.host_string)
    # At this point we should be reconnected to the newly rebooted server.
