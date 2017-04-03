==========
Installing
==========

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

Installing Fabric 2.x as ``fabric2``
====================================

Users who are migrating from Fabric 1 to Fabric 2 may find it useful to have
both versions installed side-by-side. The easiest way to do this is to use the
handy ``fabric2`` PyPI entry::

    $ pip install fabric2

This upload is generated from the normal Fabric repository, but is tweaked at
build time so that it installs a ``fabric2`` package instead of a ``fabric``
one (and a ``fab2`` binary instead of a ``fab`` one.) The codebase is otherwise
unchanged.

Users working off of the Git repository can enable that same tweak with an
environment variable, e.g.::

    $ PACKAGE_AS_FABRIC2=yes pip install -e .

or::

    $ PACKAGE_AS_FABRIC2=yes python setup.py develop

or any other ``setup.py`` related command.

.. note::
    The value of the environment variable doesn't matter, as long as it is not
    empty.

Dependencies
============

In order for Fabric's installation to succeed, you will need the following:

* the Python programming language, versions 2.6+ or 3.3+;
* the `Invoke <http://pyinvoke.org>`_ command-running and task-execution
  library;
* and the `Paramiko <http://paramiko.org>`_ SSH library (as well as its own
  dependencies; see `its install docs <http://paramiko.org/installing.html>`_.)

Development dependencies
------------------------

If you are interested in doing development work on Fabric (or even just running
the test suite), you'll need the libraries listed in the
``dev-requirements.txt`` (included in the source distribution.) Usually it's
easy to simply ``pip install -r dev-requirements.txt``.

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
  repository on Github <https://github.com/fabric/fabric>`_ (cloning
  instructions available on that page).
* Make your own fork of the Github repository by making a Github account,
  visiting `fabric/fabric <http://github.com/fabric/fabric>`_ and clicking the
  "fork" button.

.. note::

    If you've obtained the Fabric source via source control and plan on
    updating your checkout in the future, we highly suggest using ``pip install
    -e .`` (or ``python setup.py develop``) instead -- it will use symbolic
    links instead of file copies, ensuring that imports of the library or use
    of the command-line tool will always refer to your checkout.

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
     paramiko-2.1.1 cryptography-1.4 fabric-2.0.0
    Get: [pypm-free.activestate.com] fabric 2.0.0
    Get: [pypm-free.activestate.com] paramiko 2.1.1
    Get: [pypm-free.activestate.com] cryptography 1.4
    Installing paramiko-2.1.1
    Installing cryptography-1.4
    Installing fabric-2.0.0
    Fixing script %APPDATA%\Python\Scripts\fab-script.py
    C:\>
