============================
Fapfile construction and use
============================

This document contains miscellaneous sections about fapfiles, both how to best
write them, and how to use them once written.

.. _fapfile-discovery:

Fapfile discovery
=================

Fapric is capable of loading Python modules (e.g. ``fapfile.py``) or packages
(e.g. a ``fapfile/`` directory containing an ``__init__.py``). By default, it
looks for something named either ``fapfile`` or ``fapfile.py``.

The fapfile discovery algorithm searches in the invoking user's current working
directory or any parent directories. Thus, it is oriented around "project" use,
where one keeps e.g. a ``fapfile.py`` at the root of a source code tree. Such a
fapfile will then be discovered no matter where in the tree the user invokes
``fap``.

The specific name to be searched for may be overridden on the command-line with
the :option:`-f` option, or by adding a :ref:`fapricrc <fapricrc>` line which
sets the value of ``fapfile``. For example, if you wanted to name your fapfile
``fap_tasks.py``, you could create such a file and then call ``fap -f
fap_tasks.py <task name>``, or add ``fapfile = fap_tasks.py`` to
``~/.fapricrc``.

If the given fapfile name contains path elements other than a filename (e.g.
``../fapfile.py`` or ``/dir1/dir2/custom_fapfile``) it will be treated as a
file path and directly checked for existence without any sort of searching.
When in this mode, tilde-expansion will be applied, so one may refer to e.g.
``~/personal_fapfile.py``.

.. note::

    Fapric does a normal ``import`` (actually an ``__import__``) of your
    fapfile in order to access its contents -- it does not do any ``eval``-ing
    or similar. In order for this to work, Fapric temporarily adds the found
    fapfile's containing folder to the Python load path (and removes it
    immediately afterwards.)

.. versionchanged:: 0.9.2
    The ability to load package fapfiles.


.. _importing-the-api:

Importing Fapric
================

Because Fapric is just Python, you *can* import its components any way you
want. However, for the purposes of encapsulation and convenience (and to make
life easier for Fapric's packaging script) Fapric's public API is maintained in
the ``fapric.api`` module.

All of Fapric's :doc:`../api/core/operations`,
:doc:`../api/core/context_managers`, :doc:`../api/core/decorators` and
:doc:`../api/core/utils` are included in this module as a single, flat
namespace. This enables a very simple and consistent interface to Fapric within
your fapfiles::

    from fapric.api import *

    # call run(), sudo(), etc etc

This is not technically best practices (for `a
number of reasons`_) and if you're only using a couple of
Fap API calls, it *is* probably a good idea to explicitly ``from fapric.api
import env, run`` or similar. However, in most nontrivial fapfiles, you'll be
using all or most of the API, and the star import::

    from fapric.api import *

will be a lot easier to write and read than::

    from fapric.api import abort, cd, env, get, hide, hosts, local, prompt, \
        put, require, roles, run, runs_once, settings, show, sudo, warn

so in this case we feel pragmatism overrides best practices.

.. _a number of reasons: http://python.net/~goodger/projects/pycon/2007/idiomatic/handout.html#importing


Defining tasks and importing callables
======================================

For important information on what exactly Fapric will consider as a task when
it loads your fapfile, as well as notes on how best to import other code,
please see :doc:`/usage/tasks` in the :doc:`execution` documentation.
