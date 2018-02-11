==========
Installing
==========

Fabric is best installed via `pip <http://pip-installer.org>`_ (highly
recommended) or `easy_install
<http://wiki.python.org/moin/CheeseShopTutorial>`_ (older, but still works
fine), e.g.::

    $ pip install fabric

You may also opt to use your operating system's package manager; the package is
typically called ``fabric`` or ``python-fabric``. E.g.::

    $ sudo apt-get install fabric

Advanced users wanting to install a development version may use ``pip`` to grab
the latest master branch (as well as the dev version of the Paramiko
dependency)::

    $ pip install -e git+https://github.com/paramiko/paramiko/#egg=paramiko
    $ pip install -e git+https://github.com/fabric/fabric/#egg=fabric

.. warning::

    Development installs of Fabric, regardless of whether they involve source
    checkouts or direct ``pip`` installs, require the development version of
    Paramiko to be installed beforehand or Fabric's installation may fail.


Dependencies
============

In order for Fabric's installation to succeed, you will need three primary pieces of software:

* the Python programming language;
* the ``setuptools`` packaging/installation library;
* and the Python `Paramiko <http://paramiko.org>`_ SSH library. Paramiko's dependencies differ
  significantly between the 1.x and 2.x releases. See the `Paramiko installation docs
  <http://www.paramiko.org/installing.html>`_ for more info.

and, if using the :ref:`parallel execution mode <parallel-execution>`:

* the `multiprocessing`_ library.

If you're using Paramiko 1.12 or above, you will also need an additional
dependency for Paramiko:

* the `ecdsa <https://pypi.python.org/pypi/ecdsa/>`_ library

Please read on for important details on these -- there are a few gotchas.

Python
------

Fabric requires `Python <http://python.org>`_ version 2.5 - 2.7. Some caveats
and notes about other Python versions:

* We are not planning on supporting **Python 2.4** given its age and the number
  of useful tools in Python 2.5 such as context managers and new modules.
  That said, the actual amount of 2.5-specific functionality is not
  prohibitively large, and we would link to -- but not support -- a third-party
  2.4-compatible fork. (No such fork exists at this time, to our knowledge.)
* Fabric has not yet been tested on **Python 3.x** and is thus likely to be
  incompatible with that line of development. However, we try to be at least
  somewhat forward-looking (e.g. using ``print()`` instead of ``print``) and
  will definitely be porting to 3.x in the future once our dependencies do.

setuptools
----------

`Setuptools`_ comes with some Python installations by default; if yours doesn't,
you'll need to grab it. In such situations it's typically packaged as
``python-setuptools``, ``py25-setuptools`` or similar. Fabric may drop its
setuptools dependency in the future, or include alternative support for the
`Distribute`_ project, but for now setuptools is required for installation.

.. _setuptools: http://pypi.python.org/pypi/setuptools
.. _Distribute: http://pypi.python.org/pypi/distribute

``multiprocessing``
-------------------

An optional dependency, the ``multiprocessing`` library is included in Python's
standard library in version 2.6 and higher. If you're using Python 2.5 and want
to make use of Fabric's :ref:`parallel execution features <parallel-execution>`
you'll need to install it manually; the recommended route, as usual, is via
``pip``.  Please see the `multiprocessing PyPI page
<http://pypi.python.org/pypi/multiprocessing/>`_ for details.


.. warning::
    Early versions of Python 2.6 (in our testing, 2.6.0 through 2.6.2) ship
    with a buggy ``multiprocessing`` module that appears to cause Fabric to
    hang at the end of sessions involving large numbers of concurrent hosts.
    If you encounter this problem, either use :ref:`env.pool_size / -z
    <pool-size>` to limit the amount of concurrency, or upgrade to Python
    >=2.6.3.
    
    Python 2.5 is unaffected, as it requires the PyPI version of
    ``multiprocessing``, which is newer than that shipped with Python <2.6.3.

Development dependencies
------------------------

If you are interested in doing development work on Fabric (or even just running
the test suite), you may also need to install some or all of the following
packages:

* `git <http://git-scm.com>`_ and `Mercurial`_, in order to obtain some of the
  other dependencies below;
* `Nose <https://github.com/nose-devs/nose>`_
* `Coverage <http://nedbatchelder.com/code/modules/coverage.html>`_
* `PyLint <http://www.logilab.org/857>`_
* `Fudge <http://farmdev.com/projects/fudge/index.html>`_
* `Sphinx <http://sphinx.pocoo.org/>`_

For an up-to-date list of exact testing/development requirements, including
version numbers, please see the ``requirements.txt`` file included with the
source distribution. This file is intended to be used with ``pip``, e.g. ``pip
install -r requirements.txt``.

.. _Mercurial: http://mercurial.selenic.com/wiki/


.. _downloads:

Downloads
=========

To obtain a tar.gz or zip archive of the Fabric source code, you may visit
`Fabric's PyPI page <http://pypi.python.org/pypi/Fabric>`_, which offers manual
downloads in addition to being the entry point for ``pip`` and
``easy-install``.


.. _source-code-checkouts:

Source code checkouts
=====================

The Fabric developers manage the project's source code with the `Git
<http://git-scm.com>`_ DVCS. To follow Fabric's development via Git instead of
downloading official releases, you have the following options:

* Clone the canonical repository straight from `the Fabric organization's
  repository on Github <https://github.com/fabric/fabric>`_,
  ``git://github.com/fabric/fabric.git``
* Make your own fork of the Github repository by making a Github account,
  visiting `fabric/fabric <http://github.com/fabric/fabric>`_ and clicking the
  "fork" button.

.. note::

    If you've obtained the Fabric source via source control and plan on
    updating your checkout in the future, we highly suggest using ``python
    setup.py develop`` instead -- it will use symbolic links instead of file
    copies, ensuring that imports of the library or use of the command-line
    tool will always refer to your checkout.

For information on the hows and whys of Fabric development, including which
branches may be of interest and how you can help out, please see the
:doc:`development` page.


.. _pypm:

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
