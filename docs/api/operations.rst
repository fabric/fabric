==========
Operations
==========

.. automodule:: fabric.operations
    :members:
    :exclude-members: sudo, put, run, get

    .. autofunction:: sudo(command, shell=True, user=None)
    .. autofunction:: put(local_path, remote_path, mode=None)
    .. autofunction:: run(command, shell=True)
    .. autofunction:: get(remote_path, local_path)
