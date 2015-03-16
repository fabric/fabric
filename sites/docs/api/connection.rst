==============
``connection``
==============

.. automodule:: fabric.connection

.. py:data:: fabric.connection.default_config

    Default configuration object (an `invoke.config.Config`) storing root
    values and behavior toggles.

    .. warning::
        Modifying this object will result in a severe lack of support from the
        maintainers! Use CLI flags or custom Config objects if you need to
        change these values globally.

    Specific default values:

    * ``port``: TCP port number to which `.Connection` objects connect when not
      otherwise specified. Default: ``22``.
    * ``user``: Username given to the remote ``sshd`` when connecting. Default:
      your local username.
