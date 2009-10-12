============================
Fabfile construction and use
============================

Odds and ends about recommended ways to build your fabfile(s). These are just
recommendations -- as always, Fabric is just Python!

Also include: note about how Fabric discovers fabfiles. See docstrings.




Importing Fabric itself
=======================

Simplest method, which is not PEP8-compliant (meaning it's not best practices)::

    from fabric.api import *

Slightly better, albeit verbose, method which *is* PEP8-compliant::

    from fabric.api import run, sudo, prompt, abort, ...

.. note::
    You can also import directly from the individual submodules, e.g. ``from
    fabric.utils import abort``. However, all of Fabric's public API is
    available via `fabric.api` for convenience purposes.
