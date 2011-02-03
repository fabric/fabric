"""
Useful non-core functionality, e.g. functions composing multiple operations.
"""

from os import getcwd, sep
import os.path
from datetime import datetime
from tempfile import mkdtemp

from fabric.network import needs_host
from fabric.operations import local, run, put
from fabric.state import env, output

__all__ = ['rsync_project', 'upload_project']

@needs_host
def rsync_project(remote_dir, local_dir=None, exclude=(), delete=False,
    extra_opts=''):
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

    ``rsync_project()`` takes the following parameters:

    * ``remote_dir``: the only required parameter, this is the path to the
      **parent** directory on the remote server; the project directory will be
      created inside this directory. For example, if one's project directory is
      named ``myproject`` and one invokes ``rsync_project('/home/username/')``,
      the resulting project directory will be ``/home/username/myproject/``.
    * ``local_dir``: by default, ``rsync_project`` uses your current working
      directory as the source directory; you may override this with
      ``local_dir``, which should be a directory path, or list of paths in a
      single string.
    * ``exclude``: optional, may be a single string, or an iterable of strings,
      and is used to pass one or more ``--exclude`` options to ``rsync``.
    * ``delete``: a boolean controlling whether ``rsync``'s ``--delete`` option
      is used. If True, instructs ``rsync`` to remove remote files that no
      longer exist locally. Defaults to False.
    * ``extra_opts``: an optional, arbitrary string which you may use to pass
      custom arguments or options to ``rsync``.

    Furthermore, this function transparently honors Fabric's port and SSH key
    settings. Calling this function when the current host string contains a
    nonstandard port, or when ``env.key_filename`` is non-empty, will use the
    specified port and/or SSH key filename(s).

    For reference, the approximate ``rsync`` command-line call that is
    constructed by this function is the following::

        rsync [--delete] [--exclude exclude[0][, --exclude[1][, ...]]] \\
            -pthrvz [extra_opts] <local_dir> <host_string>:<remote_dir>

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
    if env.key_filename:
        keys = env.key_filename
        # For ease of use, coerce stringish key filename into list
        if not isinstance(env.key_filename, (list, tuple)):
            keys = [keys]
        key_string = "-i " + " -i ".join(keys)
    # Honor nonstandard port
    port_string = ("-p %s" % env.port) if (env.port != '22') else ""
    # RSH
    rsh_string = ""
    if key_string or port_string:
        rsh_string = "--rsh='ssh %s %s'" % (port_string, key_string)
    # Set up options part of string
    options_map = {
        'delete': '--delete' if delete else '',
        'exclude': exclude_opts % exclusions,
        'rsh': rsh_string,
        'extra': extra_opts
    }
    options = "%(delete)s%(exclude)s -pthrvz %(extra)s %(rsh)s" % options_map
    # Get local directory
    if local_dir is None:
        local_dir = '../' + getcwd().split(sep)[-1]
    # Create and run final command string
    cmd = "rsync %s %s %s@%s:%s" % (options, local_dir, env.user,
        env.host, remote_dir)
    if output.running:
        print("[%s] rsync_project: %s" % (env.host_string, cmd))
    return local(cmd)


def upload_project(local_dir=None, remote_dir=""):
    """
    Upload the current project to a remote system, tar/gzipping during the move.

    This function makes use of the ``tar`` and ``gzip`` programs/libraries, thus
    it will not work too well on Win32 systems unless one is using Cygwin or
    something similar.

    ``upload_project`` will attempt to clean up the local and remote tarfiles
    when it finishes executing, even in the event of a failure.

    :param local_dir: default current working directory, the project folder to
        upload

    """
    if not local_dir:
        local_dir = os.getcwd()

    # Remove final '/' in local_dir so that basename() works
    local_dir = local_dir.strip(os.sep)

    local_path, local_name = os.path.split(local_dir)

    tar_file = "%s.tar.gz" % local_name
    target_tar = os.path.join(remote_dir, tar_file)

    tmp_folder = mkdtemp()
    try:
        tar_path = os.path.join(tmp_folder, tar_file)
        local("tar -czf %s -C %s %s" % (tar_path, local_path, local_name))
        put(tar_path, target_tar)
        
        try:
            run("tar -xzf %s" % tar_file)

        finally:
            run("rm -f %s" % tar_file)

    finally:
        local("rm -rf %s" % tmp_folder)

