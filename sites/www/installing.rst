==========
Installing
==========

.. note::
    Users looking to install Fabric 1.x should see :doc:`installing-1.x`.
    However, :doc:`upgrading <upgrading>` to 2.x is strongly recommended.

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


.. _installing-as-fabric2:

Installing modern Fabric as ``fabric2``
=======================================

Users who are migrating from Fabric 1 to Fabric 2+ may find it useful to have
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

.. note::
    The value of the environment variable doesn't matter, as long as it is not
    empty.

``fabric`` and ``fabric2`` vs ``fabric3``
-----------------------------------------

Unfortunately, the ``fabric3`` entry on PyPI is an unauthorized fork of Fabric
1.x which we do not control. Once modern Fabric gets up to 3.x, 4.x etc, we'll
likely continue distributing it via both ``fabric`` and ``fabric2`` for
convenience; there will never be any official ``fabric3``, ``fabric4`` etc.

In other words, ``fabric2`` is purely there to help users of 1.x cross the 2.0
"major rewrite" barrier; future major versions will *not* be large rewrites and
will only have small sets of backward incompatibilities.

Inability to ``pip install -e`` both versions
---------------------------------------------

You may encounter issues if *both* versions of Fabric are installed via ``pip
install -e``, due to how that functionality works (tl;dr it just adds the
checkout directories to ``sys.path``, regardless of whether you wanted to
"install" all packages within them - so Fabric 2+'s ``fabric/`` package still
ends up visible to the import system alongside ``fabric2/``).

Thus, you may only have one of the local copies of Fabric installed in
'editable' fashion at a time, and the other must be repeatedly reinstalled via
``pip install`` (no ``-e``) if you need to make edits to it.

Order of installations
----------------------

Due to the same pip quirk mentioned above, if either of your Fabric versions
are installed in 'editable' mode, you **must** install the 'editable' version
first, and then install the 'static' version second.

For example, if you're migrating from some public release of Fabric 1 to a
checkout of modern Fabric::

    $ PACKAGE_AS_FABRIC2=yes pip install -e /path/to/fabric2
    $ pip install fabric==1.14.0

You may see some warnings on that second ``pip install`` (eg ``Not uninstalling
fabric`` or ``Can't uninstall 'fabric'``) but as long as it exits cleanly and
says something like ``Successfully installed fabric-1.14.0``, you should be
okay. Double check with e.g. ``pip list`` and you should have entries for both
``fabric`` and ``fabric2``.


Dependencies
============

In order for Fabric's installation to succeed, you will need the following:

* the Python programming language, versions 2.7 or 3.4+;
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
`Fabric's PyPI page <https://pypi.org/project/fabric>`_, which offers manual
downloads in addition to being the entry point for ``pip``.


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
