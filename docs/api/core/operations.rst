==========
Operations
==========

.. automodule:: fabric.operations
    :members:
    :exclude-members: sudo, put, run, get

    .. autofunction:: get(remote_path, local_path)
    .. autofunction:: put(local_path, remote_path, mode=None)
    .. autofunction:: run(command, shell=True, pty=False)
    .. autofunction:: sudo(command, shell=True, pty=False,user=None)
