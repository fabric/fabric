==========
Operations
==========

.. automodule:: fabric.operations
    :members:

    .. autofunction:: get(remote_path, local_path=None)
    .. autofunction:: open_shell(command=None)
    .. autofunction:: put(local_path, remote_path, use_sudo=False, mirror_local_mode=False, mode=None)
    .. autofunction:: reboot(wait=120)
    .. autofunction:: run(command, shell=True, pty=True, combine_stderr=True)
    .. autofunction:: sudo(command, shell=True, pty=True, combine_stderr=True, user=None)
