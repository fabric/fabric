============
Installation
============

The most direct way to install Fabric is to obtain the source code and run
``python setup.py install``. This method works for both release versions and
development versions of the code, and requires nothing but a basic Python
installation.

.. note::

    If you've obtained the Fabric source via source control and plan on
    updating your checkout in the future, we highly suggest using ``python
    setup.py develop`` instead -- it will use symbolic links instead of file
    copies, ensuring that imports of the library or use of the command-line
    tool will always refer to your checkout. 

Dependencies
============

In order to install Fabric, you will need `Python <http://python.org>`_ version
2.5 or newer, and the following third-party Python packages:

* `Paramiko <http://www.lag.net/paramiko/>`_ >=1.7
* `PyCrypto <http://www.amk.ca/python/code/crypto.html>`_ (a dependency of
  Paramiko) >=1.9

.. note::

    Installation via ``pip`` or ``easy_install`` (see :ref:`easy-install`
    below) will automatically install the above packages, so you may not need
    to hunt for them yourself.

.. note::

    Windows users without an installed C compiler will likely experience
    problems installing PyCrypto, as it involves C code and is not a pure
    Python package like the others. We recommend either installing a C
    development environment such as `Cygwin <http://cygwin.com>`_ or obtaining
    a precompiled Win32 PyCrypto package from `voidspace's Python modules page
    <http://www.voidspace.org.uk/python/modules.shtml#pycrypto>`_.

If you are interested in doing development work on Fabric, you may also need to
install some or all of the following packages:

* `Nose <http://code.google.com/p/python-nose/>`_ >=0.10 
* `Coverage <http://nedbatchelder.com/code/modules/coverage.html>`_ >=2.85
* `PyLint <http://www.logilab.org/857>`_ >=0.18
* `Fudge <http://farmdev.com/projects/fudge/index.html>`_ >=0.9.2
* `Sphinx <http://sphinx.pocoo.org/>`_ >= 0.6.1

Downloads
=========

To obtain a tar.gz or zip archive of the Fabric source code, you may visit
either of the following locations:

* The official downloads are available via `git.fabfile.org
  <http://git.fabfile.org>`_. Our Git repository viewer provides downloads of
  all tagged releases. See the "Download" column, next to the "Tag" column in
  the middle of the front page.
* Alternately, see `Fabric's PyPI page <http://pypi.python.org/pypi/Fabric>`_.

.. _source-code-checkouts:

Source code checkouts
=====================

The Fabric developers manage the project's source code with the `Git
<http://git-scm.com>`_ DVCS. To follow Fabric's development via Git instead of
downloading official releases, you have the following options:

* Clone the canonical Git repository, ``git://fabfile.org/fabric.git`` (note
  that a Web view of this repository can be found at `git.fabfile.org
  <http://git.fabfile.org>`_)
* Clone the official Github mirror/collaboration repository,
  ``git://github.com/bitprophet/fabric.git``
* Make your own fork of the Github repository by making a Github account,
  visiting `GitHub/bitprophet/fabric <http://github.com/bitprophet/fabric>`_
  and clicking the "fork" button.

For information on the hows and whys of Fabric development, including which
branches may be of interest and how you can help out, please see the
:doc:`development` page.

.. _easy-install:

Easy_install and Pip
====================

Fabric tries hard to play nice with packaging systems such as Python's
``setuptools``, and as such it may be installed via either `easy_install
<http://wiki.python.org/moin/CheeseShopTutorial>`_ or `pip
<http://pip.openplans.org>`_.

Fabric's source distribution also comes with a ``pip`` requirements file
called ``requirements.txt``, containing the various development requirements
listed above. At time of writing, some of the listed third-party packages
don't play well with ``pip``, so we aren't officially recommending use of the
requirements file just yet.
