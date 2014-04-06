===================
Development roadmap
===================

This document outlines Fabric's intended development path. Please make sure
you're reading `the latest version
<http://docs.fabfile.org/en/latest/roadmap.html>`_ of this document! 

.. warning::
    This information is subject to change without warning, and should not be
    used as a basis for any life- or career-altering decisions!

Fabric 1.x
==========

Fabric 1.x, while not end-of-life'd, has reached a tipping point regarding
internal tech debt & ability to make significant improvements without harming
backwards compatibility.

As such, future 1.x releases (**1.6** onwards) will emphasize small-to-medium
features (new features not requiring major overhauls of the internals) and
bugfixes.

Invoke, Fabric 2.x and Patchwork
================================

While 1.x moves on as above, we are working on a reimagined 2.x version of the
tool, and plan to:

* Finish and release `the Invoke tool/library
  <https://github.com/pyinvoke/invoke>`_ (see also :issue:`565`), which is a
  revamped and standalone version of Fabric's task running components. 

    * Initially it will be basic, matching Fabric's current functionality, but
      with a cleaner base to build on.
    * Said cleaner base then gives us a jumping-off point for new task-oriented
      features such as before/after hooks / call chains, task collections,
      improved namespacing and so forth.

* Start putting together Fabric 2.0, a partly/mostly rewritten Fabric core:

    * Leverage Invoke for task running, which will leave Fabric itself much
      more library oriented.
    * Implement object-oriented hosts/host lists and all the fun stuff that
      provides (e.g. no more hacky host string and unintuitive env var
      manipulation.)
    * No (or optional & non-default) shared state.
    * Any other core overhauls difficult to do in a backwards compatible
      fashion.
    * `Current issue list
      <https://github.com/fabric/fabric/issues?labels=2.x>`_

* Spin off ``fabric.contrib.*`` into a standalone "super-Fabric" (as in, "above Fabric") library, `Patchwork <https://github.com/fabric/patchwork>`_.

    * This lets core "execute commands on hosts" functionality iterate
      separately from "commonly useful shortcuts using Fabric core".
    * Lots of preliminary work & prior-art scanning has been done in
      :issue:`461`.
    * A public-but-alpha codebase for Patchwork exists as we think about the
      API, and is currently based on Fabric 1.x. It will likely be Fabric 2.x
      based by the time it is stable.
