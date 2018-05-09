.. _roadmap:

===================
Development roadmap
===================

This document outlines Fabric's intended development path. Please make sure
you're reading `the latest version <http://fabfile.org/roadmap.html>`_ of this
document, and also see the page about :ref:`upgrading <upgrading>` if you are
migrating from version 1 to versions 2 or above.

Fabric 2 and above
==================

Modern Fabric versions (2+) receive active feature and bugfix development:

- **2.0**: Initial public release, arguably a technology preview and a
  packaging/upgrade trial. Intent is to act as a jolt for users of 1.x who
  aren't pinning their dependencies (sorry, folks!), enable installation
  via PyPI so users don't have to install via Git to start upgrading, and
  generally get everything above-board and iterating in classic semantic
  versioning fashion.
- **2.1, 2.2, 2.3, etc**: Implement the most pressing "missing features",
  including features which were present in 1.0 (see :ref:`upgrading` for
  details on these) as well as any brand new features we've been wanting in 2.x
  for a while (though most of these will come via Invoke and/or Paramiko
  releases -- see note below for more).
- **3.0, 4.0, etc**: Subsequent major releases will **not** be full-on rewrites
  as 2.0 was, but will be *small* (feature-release-sized) releases that just
  happen to contain one or more backwards incompatible API changes. These will
  be clearly marked in the changelog and reflected in the upgrading
  documentation.

.. note::
    Many features that you may use via Fabric will only need development in the
    libraries Fabric wraps -- `Invoke <http://pyinvoke.org>`_ and `Paramiko
    <http://paramiko.org>`_ -- and unless Fabric itself needs changes to match,
    you can often get new features by upgrading only one of the three. Make
    sure to check the other projects' changelogs periodically!

Fabric 1.x
==========

Fabric 1.x has reached a tipping point regarding internal tech debt, lack of
testability & ability to make improvements without harming backwards
compatibility. As such, the 1.x line now receives bugfixes only. We
**strongly** encourage all users to :ref:`upgrade <upgrading>` to Fabric 2.x.
