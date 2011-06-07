============================
Fabfile construction and use
============================

This document contains miscellaneous sections about fabfiles, both how to best
write them, and how to use them once written.

.. _fabfile-discovery:

Fabfile discovery
=================

Fabric is capable of loading Python modules (e.g. ``fabfile.py``) or packages
(e.g. a ``fabfile/`` directory containing an ``__init__.py``). By default, it
looks for something named either ``fabfile`` or ``fabfile.py``.

The fabfile discovery algorithm searches in the invoking user's current working
directory or any parent directories. Thus, it is oriented around "project" use,
where one keeps e.g. a ``fabfile.py`` at the root of a source code tree. Such a
fabfile will then be discovered no matter where in the tree the user invokes
``fab``.

The specific name to be searched for may be overridden on the command-line with
the :option:`-f` option, or by adding a :ref:`fabricrc <fabricrc>` line which
sets the value of ``fabfile``. For example, if you wanted to name your fabfile
``fab_tasks.py``, you could create such a file and then call ``fab -f
fab_tasks.py <task name>``, or add ``fabfile = fab_tasks.py`` to
``~/.fabricrc``.

If the given fabfile name contains path elements other than a filename (e.g.
``../fabfile.py`` or ``/dir1/dir2/custom_fabfile``) it will be treated as a
file path and directly checked for existence without any sort of searching.
When in this mode, tilde-expansion will be applied, so one may refer to e.g.
``~/personal_fabfile.py``.

.. note::

    Fabric does a normal ``import`` (actually an ``__import__``) of your
    fabfile in order to access its contents -- it does not do any ``eval``-ing
    or similar. In order for this to work, Fabric temporarily adds the found
    fabfile's containing folder to the Python load path (and removes it
    immediately afterwards.)

.. versionchanged:: 0.9.2
    The ability to load package fabfiles.


.. _importing-the-api:

Importing Fabric
================

Because Fabric is just Python, you *can* import its components any way you
want. However, for the purposes of encapsulation and convenience (and to make
life easier for Fabric's packaging script) Fabric's public API is maintained in
the ``fabric.api`` module.

All of Fabric's :doc:`../api/core/operations`,
:doc:`../api/core/context_managers`, :doc:`../api/core/decorators` and
:doc:`../api/core/utils` are included in this module as a single, flat
namespace. This enables a very simple and consistent interface to Fabric within
your fabfiles::

    from fabric.api import *

    # call run(), sudo(), etc etc

This is not technically best practices (for `a
number of reasons`_) and if you're only using a couple of
Fab API calls, it *is* probably a good idea to explicitly ``from fabric.api
import env, run`` or similar. However, in most nontrivial fabfiles, you'll be
using all or most of the API, and the star import::

    from fabric.api import *

will be a lot easier to write and read than::

    from fabric.api import abort, cd, env, get, hide, hosts, local, prompt, \
        put, require, roles, run, runs_once, settings, show, sudo, warn

so in this case we feel pragmatism overrides best practices.

.. _a number of reasons: http://python.net/~goodger/projects/pycon/2007/idiomatic/handout.html#importing


Defining tasks and importing callables
======================================

For important information on what exactly Fabric will consider as a task when
it loads your fabfile, as well as notes on how best to import other code,
please see :doc:`/usage/tasks` in the :doc:`execution` documentation.
