==========
Operations
==========

.. automodule:: fabric.operations
    :members:
    :exclude-members: sudo, put, run, get

    .. autofunction:: sudo(command, shell=True, user=None, pty=False)
    .. autofunction:: put(local_path, remote_path, mode=None)
    .. autofunction:: run(command, shell=True, pty=False)
    .. autofunction:: get(remote_path, local_path)
