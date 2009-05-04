============
Installation
============

Manual installation
===================

The most direct way to install Fabric is to obtain the source code and run
``python setup.py install``. This method works for both release versions and
development versions of the code, and requires nothing but a basic Python
installation.

.. note::

    If you've obtained the Fabric source via source control and plan on updating
    often, we highly suggest doing ``python setup.py develop`` instead -- it
    will use symlinks instead of file copies. Thus, whenever you ``import
    fabric`` or run the ``fab`` tool, your checked-out copy of the code will be
    used, with no need to use ``setup.py`` every time something changes.

Dependencies
------------

In order to install Fabric manually, you will need to obtain and install the
following packages which Fabric needs in order to run:

* `Paramiko <http://www.lag.net/paramiko/>`_ >=1.7

If you are interested in doing any development work on Fabric, you will also
want the following dev-related packages:

* `Nose <http://code.google.com/p/python-nose/>`_ >=0.10 
* `Coverage <http://nedbatchelder.com/code/modules/coverage.html>`_ >=2.85
* `PyLint <http://www.logilab.org/857>`_ >=0.18
* `Fudge <http://farmdev.com/projects/fudge/index.html>`_ >=0.9.2
* `Sphinx <http://sphinx.pocoo.org/>`_ >= 0.6.1

Archive downloads
-----------------

To obtain a tar.gz or zip archive of the Fabric source code, you may visit
either of the following locations:

* The official downloads are available via `git.fabfile.org
  <http://git.fabfile.org>`_. Our Git repository viewer provides downloads of
  all tagged releases. See the "Download" column, next to the "Tag" column in
  the middle of the front page.
* Alternately, see `Fabric's PyPI page <http://pypi.python.org/pypi/Fabric>`_.

Source code checkouts
---------------------

To track Fabric's source development, see the :doc:`development` page.


Easy_install
============

Part of Python's ``setuptools`` library, ``easy_install`` provides an automatic
alternative to the manual "download archive, unpack archive, setup.py install"
process. It will also attempt to download and install any dependencies.
