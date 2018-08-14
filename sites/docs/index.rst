==================================
Welcome to Fabric's documentation!
==================================

This site covers Fabric's usage & API documentation. For basic info on what
Fabric is, including its public changelog & how the project is maintained,
please see `the main project website <http://fabfile.org>`_.

Getting started
---------------

Many core ideas & API calls are explained in the tutorial/getting-started
document:

.. toctree::
    :maxdepth: 2

    getting-started

Upgrading from 1.x
------------------

Looking to upgrade from Fabric 1.x? See our :ref:`detailed upgrade guide
<upgrading>` on the nonversioned main project site.

.. _concepts-docs:

Concepts
--------

Dig deeper into specific topics:

.. toctree::
    :maxdepth: 2
    :glob:

    concepts/*

The ``fab`` CLI tool
--------------------

Details on the CLI interface to Fabric, how it extends Invoke's CLI machinery,
and examples of shortcuts for executing tasks across hosts or groups.

.. toctree::
    cli

.. _api-docs:

API
---

Know what you're looking for & just need API details? View our auto-generated
API documentation:

.. toctree::
    :maxdepth: 1
    :glob:

    api/*
