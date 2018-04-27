===================
Development roadmap
===================

This document outlines Fabric's intended development path. Please make sure
you're reading `the latest version <http://fabfile.org/roadmap.html>`_ of this
document, and also see the page about :ref:`upgrading <upgrading>` if you are
migrating from version 1 to versions 2 or above.

Fabric 2 and above
==================

Modern Fabric versions (2+) receive active feature development. At the present
time, version 2 has only recently been released and we are still porting 
functionality from 1.x that was not part of 2.0 -- see :ref:`upgrading` for
details. This will make up the early 2.x feature releases: 2.1, 2.2, 2.3, etc.

As things mature and/or we tackle larger features, we may need to make
backwards incompatible changes -- which will generate Fabric 3.0, 4.0 etc.
These will *not* be rewrites, and the scope of these changes will be kept
minimal so that upgrading is relatively easy.

.. note::
    Many features that you may use via Fabric will only need development in the
    libraries Fabric wraps -- `Invoke <http://pyinvoke.org>`_ and `Paramiko
    <http://paramiko.org>`_ -- and unless Fabric itself needs changes to match,
    you can often get away with only upgrading one of them at a time. Make sure
    to check the other projects' changelogs periodically!

Fabric 1.x
==========

Fabric 1.x has reached a tipping point regarding internal tech debt & ability
to make significant improvements without harming backwards compatibility. As
such, the 1.x line now receives bugfixes only. We **strongly** encourage all
users to :ref:`upgrade <upgrading>` to Fabric 2.x.
