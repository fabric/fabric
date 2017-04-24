"""
Useful non-core functionality, e.g. functions composing multiple operations.
"""
from __future__ import with_statement

from os import getcwd, sep
import os.path
from tempfile import mkdtemp

from fabric.network import needs_host, key_filenames, normalize
from fabric.operations import local, run, sudo, put
from fabric.state import env, output
from fabric.context_managers import cd

__all__ = ['rsync_project', 'upload_project']

@needs_host
def rsync_project(
    remote_dir,
    local_dir=None,
    exclude=(),
    delete=False,
    extra_opts='',
    ssh_opts='',
    capture=False,
    upload=True,
    default_opts='-pthrvz'
):
    """
    Synchronize a remote directory with the current project directory via rsync.

    Where ``upload_project()`` makes use of ``scp`` to copy one's entire
    project every time it is invoked, ``rsync_project()`` uses the ``rsync``
    command-line utility, which only transfers files newer than those on the
    remote end.

    ``rsync_project()`` is thus a simple wrapper around ``rsync``; for
    details on how ``rsync`` works, please see its manpage. ``rsync`` must be
    installed on both your local and remote systems in order for this operation
    to work correctly.

    This function makes use of Fabric's ``local()`` operation, and returns the
    output of that function call; thus it will return the stdout, if any, of
    the resultant ``rsync`` call.

    ``rsync_project()`` uses the current Fabric connection parameters (user,
    host, port) by default, adding them to rsync's ssh options (then mixing in
    ``ssh_opts``, if given -- see below.)

    ``rsync_project()`` takes the following parameters:

    * ``remote_dir``: the only required parameter, this is the path to the
      directory on the remote server. Due to how ``rsync`` is implemented, the
      exact behavior depends on the value of ``local_dir``:

        * If ``local_dir`` ends with a trailing slash, the files will be
          dropped inside of ``remote_dir``. E.g.
          ``rsync_project("/home/username/project/", "foldername/")`` will drop
          the contents of ``foldername`` inside of ``/home/username/project``.
        * If ``local_dir`` does **not** end with a trailing slash (and this
          includes the default scenario, when ``local_dir`` is not specified),
          ``remote_dir`` is effectively the "parent" directory, and a new
          directory named after ``local_dir`` will be created inside of it. So
          ``rsync_project("/home/username", "foldername")`` would create a new
          directory ``/home/username/foldername`` (if needed) and place the
          files there.

    * ``local_dir``: by default, ``rsync_project`` uses your current working
      directory as the source directory. This may be overridden by specifying
      ``local_dir``, which is a string passed verbatim to ``rsync``, and thus
      may be a single directory (``"my_directory"``) or multiple directories
      (``"dir1 dir2"``). See the ``rsync`` documentation for details.
    * ``exclude``: optional, may be a single string, or an iterable of strings,
      and is used to pass one or more ``--exclude`` options to ``rsync``.
    * ``delete``: a boolean controlling whether ``rsync``'s ``--delete`` option
      is used. If True, instructs ``rsync`` to remove remote files that no
      longer exist locally. Defaults to False.
    * ``extra_opts``: an optional, arbitrary string which you may use to pass
      custom arguments or options to ``rsync``.
    * ``ssh_opts``: Like ``extra_opts`` but specifically for the SSH options
      string (rsync's ``--rsh`` flag.)
    * ``capture``: Sent directly into an inner `~fabric.operations.local` call.
    * ``upload``: a boolean controlling whether file synchronization is
      performed up or downstream. Upstream by default.
    * ``default_opts``: the default rsync options ``-pthrvz``, override if
      desired (e.g. to remove verbosity, etc).

    Furthermore, this function transparently honors Fabric's port and SSH key
    settings. Calling this function when the current host string contains a
    nonstandard port, or when ``env.key_filename`` is non-empty, will use the
    specified port and/or SSH key filename(s).

    For reference, the approximate ``rsync`` command-line call that is
    constructed by this function is the following::

        rsync [--delete] [--exclude exclude[0][, --exclude[1][, ...]]] \\
            [default_opts] [extra_opts] <local_dir> <host_string>:<remote_dir>

    .. versionadded:: 1.4.0
        The ``ssh_opts`` keyword argument.
    .. versionadded:: 1.4.1
        The ``capture`` keyword argument.
    .. versionadded:: 1.8.0
        The ``default_opts`` keyword argument.
    """
    # Turn single-string exclude into a one-item list for consistency
    if not hasattr(exclude, '__iter__'):
        exclude = (exclude,)
    # Create --exclude options from exclude list
    exclude_opts = ' --exclude "%s"' * len(exclude)
    # Double-backslash-escape
    exclusions = tuple([str(s).replace('"', '\\\\"') for s in exclude])
    # Honor SSH key(s)
    key_string = ""
    keys = key_filenames()
    if keys:
        key_string = "-i " + " -i ".join(keys)
    # Port
    user, host, port = normalize(env.host_string)
    port_string = "-p %s" % port
    # RSH
    rsh_string = ""
    if env.gateway is None:
        gateway_opts = ""
    else:
        gw_user, gw_host, gw_port = normalize(env.gateway)
        gw_str = "-A -o \"ProxyCommand=ssh %s -p %s %s@%s nc %s %s\""
        gateway_opts = gw_str % (
            key_string, gw_port, gw_user, gw_host, host, port
        )

    rsh_parts = [key_string, port_string, ssh_opts, gateway_opts]
    if any(rsh_parts):
        rsh_string = "--rsh='ssh %s'" % " ".join(rsh_parts)
    # Set up options part of string
    options_map = {
        'delete': '--delete' if delete else '',
        'exclude': exclude_opts % exclusions,
        'rsh': rsh_string,
        'default': default_opts,
        'extra': extra_opts,
    }
    options = "%(delete)s%(exclude)s %(default)s %(extra)s %(rsh)s" % options_map
    # Get local directory
    if local_dir is None:
        local_dir = '../' + getcwd().split(sep)[-1]
    # Create and run final command string
    if host.count(':') > 1:
        # Square brackets are mandatory for IPv6 rsync address,
        # even if port number is not specified
        remote_prefix = "[%s@%s]" % (user, host)
    else:
        remote_prefix = "%s@%s" % (user, host)
    if upload:
        cmd = "rsync %s %s %s:%s" % (options, local_dir, remote_prefix, remote_dir)
    else:
        cmd = "rsync %s %s:%s %s" % (options, remote_prefix, remote_dir, local_dir)

    if output.running:
        print("[%s] rsync_project: %s" % (env.host_string, cmd))
    return local(cmd, capture=capture)


def upload_project(local_dir=None, remote_dir="", use_sudo=False):
    """
    Upload the current project to a remote system via ``tar``/``gzip``.

    ``local_dir`` specifies the local project directory to upload, and defaults
    to the current working directory.

    ``remote_dir`` specifies the target directory to upload into (meaning that
    a copy of ``local_dir`` will appear as a subdirectory of ``remote_dir``)
    and defaults to the remote user's home directory.

    ``use_sudo`` specifies which method should be used when executing commands
    remotely. ``sudo`` will be used if use_sudo is True, otherwise ``run`` will
    be used.

    This function makes use of the ``tar`` and ``gzip`` programs/libraries,
    thus it will not work too well on Win32 systems unless one is using Cygwin
    or something similar. It will attempt to clean up the local and remote
    tarfiles when it finishes executing, even in the event of a failure.

    .. versionchanged:: 1.1
        Added the ``local_dir`` and ``remote_dir`` kwargs.

    .. versionchanged:: 1.7
        Added the ``use_sudo`` kwarg.
    """
    runner = use_sudo and sudo or run

    local_dir = local_dir or os.getcwd()

    # Remove final '/' in local_dir so that basename() works
    local_dir = local_dir.rstrip(os.sep)

    local_path, local_name = os.path.split(local_dir)
    local_path = local_path or '.'
    tar_file = "%s.tar.gz" % local_name
    target_tar = os.path.join(remote_dir, tar_file)
    tmp_folder = mkdtemp()

    try:
        tar_path = os.path.join(tmp_folder, tar_file)
        local("tar -czf %s -C %s %s" % (tar_path, local_path, local_name))
        put(tar_path, target_tar, use_sudo=use_sudo)
        with cd(remote_dir):
            try:
                runner("tar -xzf %s" % tar_file)
            finally:
                runner("rm -f %s" % tar_file)
    finally:
        local("rm -rf %s" % tmp_folder)
