============
Installation
============

The most direct way to install Fabric is to obtain the source code and run
``python setup.py install``. This method works for both release and development
versions of the code, and requires nothing but a basic Python installation.

.. note::

    If you've obtained the Fabric source via source control and plan on
    updating your checkout in the future, we highly suggest using ``python
    setup.py develop`` instead -- it will use symbolic links instead of file
    copies, ensuring that imports of the library or use of the command-line
    tool will always refer to your checkout. 

Dependencies
============

In order to install Fabric, you will need three primary pieces of
software: the Python programming language, the Paramiko SSH library, and
the PyCrypto cryptography library (a dependency of Paramiko.) Please read
on for important details on each dependency -- there are a few gotchas.

Python
------

Fabric requires `Python <http://python.org>`_ version 2.5 or 2.6. Some caveats
and notes about other Python versions:

* We are not planning on supporting **Python 2.4** given its age and the number
  of useful tools in Python 2.5 such as context managers and new modules.
  That said, the actual amount of 2.5-specific functionality is not
  prohibitively large, and we would link to -- but not support -- a third-party
  2.4-compatible fork. (No such fork exists at this time, to our knowledge.)
* Fabric has not yet been tested on **Python 3.x** and is thus likely to be
  incompatible with that line of development. However, we try to be at least
  somewhat forward-looking (e.g. using ``print()`` instead of ``print``) and
  will definitely be porting to 3.x in the future once our dependencies and the
  rest of the ecosystem does so as well.
* A bug in **Python 2.5.0 and 2.5.1** causes errors in
  `fabric.contrib.files.upload_template` due to its combination of context
  managers and ``tempfile.NamedTemporaryFile``. The rest of Fabric will work
  fine on these Python versions, but be aware of this conflict if you do use
  `upload_template` and are running on something older than Python 2.5.2.

.. _paramiko-warning:

Paramiko
--------

`Paramiko <http://www.lag.net/paramiko/>`_ is a Python implementation of the
SSH protocol suite, and is what Fabric builds upon for its networking support.
At this time, **only Paramiko version 1.7.4 is supported!** A more recent
version, 1.7.5, is on PyPI, but contains `a serious bug
<https://bugs.launchpad.net/paramiko/+bug/413850>`_ that causes effectively
random (albeit uncommon) SSHException errors.

Furthermore, because 1.7.5 is the only version currently uploaded to PyPI (the
source of ``easy_install`` and ``pip`` installs) we do **not** recommend you
use those tools to install Fabric until you have installed Paramiko and
PyCrypto by hand.

Paramiko 1.7.4 may be downloaded from Paramiko's `old releases directory
<http://www.lag.net/paramiko/download/>`_ and installed by unpacking and
running ``python setup.py install``, as with most other Python packages.

PyCrypto
--------

`PyCrypto <http://www.amk.ca/python/code/crypto.html>`_ is a dependency of
Paramiko, providing the low-level (C-based) encryption algorithms used to run
SSH. You will need version 1.9 or newer, and may install PyCrypto from
``easy_install`` or ``pip`` without worry. However, unless you are installing
from a precompiled source such as a Debian apt repository or RedHat RPM, you
will need the ability to build Python C-based modules from source -- read on.

Users on **Unix-based platforms** such as Ubuntu or Mac OS X will need the
traditional C build toolchain installed (e.g. Developer Tools / XCode Tools on
the Mac, or the ``build-essential`` package on Ubuntu or Debian Linux --
basically, anything with ``gcc``, ``make`` and so forth) as well as the Python
development libraries, often named ``python-dev`` or similar.

For **Windows** users we recommend either installing a C development environment
such as `Cygwin <http://cygwin.com>`_ or obtaining a precompiled Win32 PyCrypto
package from `voidspace's Python modules page
<http://www.voidspace.org.uk/python/modules.shtml#pycrypto>`_.

Development dependencies
------------------------

If you are interested in doing development work on Fabric (or even just running
the test suite), you may also need to install some or all of the following
packages:

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
* `Our GitHub mirror <http://github.com/bitprophet/fabric>`_ has downloads of
  all tagged releases as well -- just click the 'Download' button near the top
  of the main page.
* `Fabric's PyPI page <http://pypi.python.org/pypi/Fabric>`_ offers manual
  downloads as well as being the entry point for :ref:`easy-install`.

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

.. warning::

    Please see the :ref:`above warning concerning Paramiko <paramiko-warning>`
    before attempting to install Fabric via ``easy_install`` or ``pip``.

Fabric's source distribution also comes with a ``pip`` requirements file
called ``requirements.txt``, containing the various development requirements
listed above (note, that's *development* requirements -- not necessary for
simply using the software.) At time of writing, some of the listed third-party
packages don't play well with ``pip``, so we aren't officially recommending use
of the requirements file just yet.
