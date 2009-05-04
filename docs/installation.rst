============
Installation
============

The most direct way to install Fabric is to obtain the source code and run
``python setup.py install``. This method works for both release versions and
development versions of the code, and requires nothing but a basic Python
installation.

.. note::

    If you've obtained the Fabric source via source control and plan on updating
    often, we highly suggest doing ``python setup.py develop`` instead -- it
    will use symlinks instead of file copies so that use of the Python library
    or command-line tool will always use your checked-out version.

Dependencies
============

In order to install Fabric, you will need Python 2.5+, and the following
third-party Python packages:

* `Paramiko <http://www.lag.net/paramiko/>`_ >=1.7
* `PyCrypto <http://www.amk.ca/python/code/crypto.html>`_ (a dependency of
  Paramiko) >=1.9

If you are interested in doing any development work on Fabric, you will also
want the following dev-related packages:

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

To track Fabric's source development, which is done via the `Git
<http://git-scm.com>`_ DVCS, you may use any of the following options:

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


Easy_install and Pip
====================

Fabric tries hard to play nice with packaging systems such as Python's
``setuptools``, and as such it may be installed via either `easy_install
<http://wiki.python.org/moin/CheeseShopTutorial>`_ or `pip
<http://pip.openplans.org>`_.

Fabric's source distribution also comes with a ``pip`` requirements file called
``requirements.txt``, containing the various development requirements listed
above. At time of writing, some of the listed third-party packages don't play
well with ``pip``, so we aren't officially recommending use of the requirements
file just yet.
