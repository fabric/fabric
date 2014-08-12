===================
Development roadmap
===================

This document outlines Fabric's intended development path. Please make sure
you're reading `the latest version
<http://fabfile.org/roadmap.html>`_ of this document! 

.. warning::
    This information is subject to change without warning, and should not be
    used as a basis for any life- or career-altering decisions!

Fabric 2.x
==========

Fabric 2.0 and above is split into a few component projects:

* `Invoke <http://pyinvoke.org>`_ provides the API for task execution
  (including via the CLI), namespacing, parallelism, and local shell commands.
  It can be used on its own; if you don't need SSH functionality, you don't
  need Fabric or its other dependencies such as Paramiko.
* `Paramiko <http://paramiko.org>`_ implements the low level SSH API, such as
  channels, transports, SSH configuration files, key management, and so forth.
* Fabric itself ties the above two projects together into a high level remote
  execution framework, focusing on concepts like server connections, file
  transfers, and invoking & managing remote shell commands.
* An optional component is `Patchwork <https://github.com/fabric/patchwork>`_
  which contains "best practices" versions of common remote actions, using the
  core Fabric API. Examples include file management, templating, wrappers
  around the ``rsync`` tool, remote system information gathering, and much
  more.

Development therefore lives in various places depending on the specific problem
domain - task namespacing, for example, will continue to improve in Invoke; new
SSH key types in Paramiko; and so forth.

Fabric 1.x
==========

Fabric 1.x has reached a tipping point regarding internal tech debt & ability
to make significant improvements without harming backwards compatibility. As
such, the 1.x line now receives bugfixes only. We **strongly** encourage all
users to upgrade to Fabric 2.x.

.. FIXME: add link to an upgrade doc
