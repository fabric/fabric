==============
``connection``
==============

.. automodule:: fabric.connection

.. py:method:: fabric.connection.Config.global_defaults

    Default configuration values and behavior toggles.

    .. warning::
        Modifying this object will result in a severe lack of support from the
        maintainers! Use CLI flags or custom Config instances if you need to
        change these values globally.

    Specific default values:

    * ``port``: TCP port number to which `.Connection` objects connect when not
      otherwise specified. Default: ``22``.
    * ``user``: Username given to the remote ``sshd`` when connecting. Default:
      your local username.
