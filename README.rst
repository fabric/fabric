Fabric3 is a Python (2.7 or 3.4+) library and command-line tool for
streamlining the use of SSH for application deployment or systems
administration tasks. This is a fork of the original
`Fabric <http://www.fabfile.org/>`_ (`git <https://github.com/fabric/fabric>`_) with
the intention of providing support for Python3, while maintaining support for
all non-archaic versions if Python2.  Please see below for known differences
with the upstream version of Fabric. To switch to Fabric3, simply do::

   pip uninstall Fabric
   pip install Fabric3

... and don't forget to update any requirements.txt files accordingly::

   # Fabric==1.10.2
   Fabric3==1.10.2.post2

It provides a basic suite of operations for executing local or remote shell
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

In addition to use via the ``fab`` tool, Fabric3's components may be imported
into other Python code, providing a Pythonic interface to the SSH protocol
suite at a higher level than that provided by e.g. the ``Paramiko`` library
(which Fabric3 itself uses.)

Differences with Fabric
=======================

Generally this project aims to be a drop-in replacement for Fabric and will
periodically merge any changes from the upstream project. Any differences are
noted here:

* The release installs as `Fabric3`. Despite it's name, this version is tested
  with Python2.7 and Python 3.4+.
* Versioning is based on upstream Fabric releases, with a `postX` appended. So
  version "1.10.2.post2" is equivalent to Fabrics own "1.10.2" release.
* `fabric.utils.RingBuffer` is removed, use `collections.deque` from the
  standard library instead.
* In Python3, Fabric3 implements its own version of `contextlib.nested` based on
  `contextlib.ExitStack`, since it's no longer available in Python3. Please note
  that it was removed with good reason, we do not encourage you use it.
* Fabric3 requires the `six` library for compatability.
* Minimum requirements for paramiko have been bumped to 1.16.0.
* There is one known issue in the test-suite (#6) that should be fixed by
  paramiko 1.16.1.

ChangeLog
---------

1.10.2.post3 (2016-02-07)
   * Cleanup imports in test suite.
   * Add Python 2/3/3.5 classifiers in setup.py.
   * Remove `fabric.utils.RingBuffer` with `collections.deque` from stdlib.
   * Remove `with_statement` future import, it does nothing in Python 2.6+.

1.10.2.post2 (2016-01-31)
   * Identify as Fabric3 on the command-line (#4).
   * Fix UnicodeDecodeError when receiving remote data (#5).
   * Require paramiko 1.16.0.
