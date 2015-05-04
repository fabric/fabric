===================
Development roadmap
===================

This document outlines Fabric's intended development path. Please make sure
you're reading `the latest version <http://fabfile.org/roadmap.html>`_ of this
document!

.. warning::
    This information is subject to change without warning, and should not be
    used as a basis for any life- or career-altering decisions!

Fabric 1.x
==========

Fabric 1.x, while not quite yet end-of-life'd, has reached a tipping point
regarding internal tech debt & ability to make improvements without harming
backwards compatibility.

As such, future 1.x releases (**1.6** onwards) will emphasize small-to-medium
features (new features not requiring major overhauls of the internals) and
bugfixes.

Invoke, Fabric 2.x and Patchwork
================================

While 1.x moves on as above, we are working on a reimagined 2.x version of the
tool, and plan to:

* Finish and release `the Invoke tool/library
  <https://github.com/pyinvoke/invoke>`_ (see also :issue:`565` and `this
  Invoke FAQ
  <http://www.pyinvoke.org/faq.html#why-was-invoke-split-off-from-the-fabric-project>`_),
  which is a revamped and standalone version of Fabric's task running
  components.

    * As of early 2015, Invoke is already reasonably mature and has a handful of
      features lacking in Fabric itself, including but not limited to:
      
        * a more explicit and powerful namespacing implementation
        * "regular" style CLI flags, including powerful tab completion
        * before/after hooks
        * explicit context management (no shared state)
        * significantly more powerful configuration mechanisms

    * Invoke is already Python 3 compatible, due to being a new codebase with
      few dependencies.
    * As Fabric 2 is developed, Invoke will approach a 1.0 release, and will
      continue to grow & change to suit Fabric's needs while remaining a high
      quality standalone task runner.

* Release Fabric 2.0, a mostly-rewritten Fabric core:

    * Leverage Invoke for task running, leaving Fabric itself much more library
      oriented.
    * Implement object-oriented hosts/host lists and all the fun stuff that
      provides (no more hacky host string and unintuitive env var
      manipulation.)
    * No more shared state by default (thanks to Invoke's context design.)
    * Any other core overhauls difficult to do in a backwards compatible
      fashion.
    * Test-driven development (Invoke does this as well.)

* Spin off ``fabric.contrib.*`` into a standalone "super-Fabric" (as in, "above
  Fabric") library, `Patchwork <https://github.com/fabric/patchwork>`_.

    * This lets core "execute commands on hosts" functionality iterate
      separately from "commonly useful shortcuts using Fabric core".
    * Lots of preliminary work & prior-art scanning has been done in
      :issue:`461`.
    * A public-but-alpha codebase for Patchwork exists as we think about the
      API, and is currently based on Fabric 1.x. It will likely be Fabric 2.x
      based by the time it is stable.
