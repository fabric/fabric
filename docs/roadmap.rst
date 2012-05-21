===================
Development roadmap
===================

This document outlines Fabric's intended development path. Please make sure
you're reading `the latest version
<http://docs.fabfile.org/en/latest/roadmap.html>`_ of this document! 

.. warning::
    This information is subject to change without warning, and should not be
    used as a basis for any life- or career-altering decisions!


Near-term feature releases and support work
===========================================

* Fabric **1.5**: SSH tunnelling, remote timeouts, improved SSH key debug info,
  ``sudo`` improvements, and a bit more. See the `milestone issues page
  <https://github.com/fabric/fabric/issues?milestone=22&state=open>`_ for what
  remains to be done.


Invoke and Fabric 2.0
=====================

* Finish and release the Invoke library, which is a revamped and standalone
  version of Fabric's task running components. See :issue:`565`.
    * Initially it will be relatively basic, matching Fabric's current
      functionality, but with a cleaner base to build on.
    * That opens the door for dependencies and so forth.
* Start putting together Fabric 2.0, a partly/mostly rewritten Fabric core:
    * Leverage Invoke for task running, which will leave Fabric itself much
      more library oriented.
    * Object-oriented hosts/host lists and all the fun stuff that provides
      (e.g. no more hacky host string and unintuitive env var manipulation.)
    * No (or optional & non-default) shared state.
    * Any other core overhauls difficult to do in a backwards compatible
      fashion.
    * `Current issue list
      <https://github.com/fabric/fabric/issues?labels=2.x>`_
