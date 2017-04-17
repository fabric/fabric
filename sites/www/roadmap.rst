===================
Development roadmap
===================

This document outlines Fabric's intended development path. Please make sure
you're reading `the latest version
<http://fabfile.org/roadmap.html>`_ of this document! 

Fabric 2.x
==========

Fabric 2 is currently in alpha; the short term roadmap is:

- Gather feedback on overall API methodology, in case major changes seem
  necessary;
- Implement the most crucial of remaining 'missing features' re: parity with
  version 1 (though anything that seems feasible to add without changing
  existing APIs, should be left til post-2.0 feature releases);
- Enter a beta period where the APIs are frozen and bugs are squashed (this
  step is optional; intent is to release more often, not less often);
- Release 2.0.0; ideally by, during or soon after PyCon US 2017 sprints.
- Prioritize 'missing features' that were left for additive feature releases,
  and put them out as 2.1, 2.2, 2.3 etc.
- If necessary (e.g. if real-world use exposes serious problems with the 2.0
  APIs), make backwards incompatible tweaks and release 3.0, 4.0, etc - without
  multi-year gaps in between. Ideally, never have more than a small amount of
  backwards incompatibility in any given jump.

Fabric 1.x
==========

Fabric 1.x has reached a tipping point regarding internal tech debt & ability
to make significant improvements without harming backwards compatibility. As
such, the 1.x line now receives bugfixes only. We **strongly** encourage all
users to :ref:`upgrade <upgrading>` to Fabric 2.x.
