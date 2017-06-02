Fabric is a Python (2.5-2.7) library and command-line tool for
streamlining the use of SSH for application deployment or systems
administration tasks. Python 3.x support is planned for a future version of Fabric,
but users who require Python 3.x support until then can use the 
`Fabric3 fork <https://pypi.python.org/pypi/Fabric3>`_ of this project.

Fabric provides a basic suite of operations for executing local or remote shell
commands (normally or via ``sudo``) and uploading/downloading files, as well as
auxiliary functionality such as prompting the running user for input, or
aborting execution.
 
Typical use involves creating a Python module containing one or more functions,
then executing them via the ``fab`` command-line tool. Below is a small but
complete "fabfile" containing a single task:

.. code-block:: python

    from fabric.api import run

    def host_type():
        run('uname -s')

If you save the above as ``fabfile.py`` (the default module that
``fab`` loads), you can run the tasks defined in it on one or more
servers, like so::

    $ fab -H localhost,linuxbox host_type
    [localhost] run: uname -s
    [localhost] out: Darwin
    [linuxbox] run: uname -s
    [linuxbox] out: Linux

    Done.
    Disconnecting from localhost... done.
    Disconnecting from linuxbox... done.

In addition to use via the ``fab`` tool, Fabric's components may be imported
into other Python code, providing a Pythonic interface to the SSH protocol
suite at a higher level than that provided by e.g. the ``Paramiko`` library
(which Fabric itself uses.)
