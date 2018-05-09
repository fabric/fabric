================
Installing (1.x)
================

.. note::
    Installing Fabric 2.0 or above? Looking for non-PyPI downloads or source
    code checkout instructions? See :doc:`installing`.

This document includes legacy notes on installing Fabric 1.x. Users are
strongly encouraged to upgrade to 2.x when possible.


Basic installation
==================

Fabric is best installed via `pip <http://pip-installer.org>`_::

    $ pip install fabric

All advanced ``pip`` use cases work too, such as::

    $ pip install -e git+https://github.com/fabric/fabric

Or cloning the Git repository and running::

    $ pip install -e .

within it.

Your operating system may also have a Fabric package available (though these
are typically older and harder to support), typically called ``fabric`` or
``python-fabric``. E.g.::

    $ sudo apt-get install fabric


Dependencies
============

In order for Fabric's installation to succeed, you will need four primary pieces of software:

* the Python programming language;
* the ``setuptools`` packaging/installation library;
* the Python `Paramiko <http://paramiko.org>`_ SSH library;
* and Paramiko's dependency, `Cryptography <https://cryptography.io>`_.

and, if using parallel execution mode,

* the `multiprocessing`_ library.

Please read on for important details on each dependency -- there are a few
gotchas.

Python
------

Fabric requires `Python <http://python.org>`_ version 2.5+.

setuptools
----------

`Setuptools`_ comes with most Python installations by default; if yours
doesn't, you'll need to grab it. In such situations it's typically packaged as
``python-setuptools``, ``py26-setuptools`` or similar.

.. _setuptools: https://pypi.org/project/setuptools

``multiprocessing``
-------------------

An optional dependency, the ``multiprocessing`` library is included in Python's
standard library in version 2.6 and higher. If you're using Python 2.5 and want
to make use of Fabric's parallel execution features you'll need to install it
manually; the recommended route, as usual, is via ``pip``.  Please see the
`multiprocessing PyPI page <https://pypi.org/project/multiprocessing/>`_ for
details.


.. warning::
    Early versions of Python 2.6 (in our testing, 2.6.0 through 2.6.2) ship
    with a buggy ``multiprocessing`` module that appears to cause Fabric to
    hang at the end of sessions involving large numbers of concurrent hosts.
    If you encounter this problem, either use ``env.pool_size`` / ``-z`` to
    limit the amount of concurrency, or upgrade to Python
    >=2.6.3.
    
    Python 2.5 is unaffected, as it requires the PyPI version of
    ``multiprocessing``, which is newer than that shipped with Python <2.6.3.


.. _pypm-1.x:

ActivePython and PyPM
=====================

Windows users who already have ActiveState's `ActivePython
<http://www.activestate.com/activepython/downloads>`_ distribution installed
may find Fabric is best installed with `its package manager, PyPM
<http://code.activestate.com/pypm/>`_. Below is example output from an
installation of Fabric via ``pypm``::

    C:\> pypm install fabric
    The following packages will be installed into "%APPDATA%\Python" (2.7):
     paramiko-1.7.8 pycrypto-2.4 fabric-1.3.0
    Get: [pypm-free.activestate.com] fabric 1.3.0
    Get: [pypm-free.activestate.com] paramiko 1.7.8
    Get: [pypm-free.activestate.com] pycrypto 2.4
    Installing paramiko-1.7.8
    Installing pycrypto-2.4
    Installing fabric-1.3.0
    Fixing script %APPDATA%\Python\Scripts\fab-script.py
    C:\>
