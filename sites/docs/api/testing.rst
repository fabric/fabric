.. _testing-subpackage:

===========
``testing``
===========

The ``fabric.testing`` subpackage contains a handful of test helper modules:

- `fabric.testing.base` which only depends on things like ``mock`` and is
  appropriate in just about any test paradigm;
- `fabric.testing.fixtures`, containing ``pytest`` fixtures and thus only of
  interest for users of ``pytest``.

All are documented below. Please note the module-level documentation which
contains install instructions!

``testing.base``
================

.. automodule:: fabric.testing.base

``testing.fixtures``
====================

.. automodule:: fabric.testing.fixtures
