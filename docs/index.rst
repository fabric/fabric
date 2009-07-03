======
Fabric
======

Work in progress!
=================

This documentation is for Fabric's currently in-development version, which will
eventually become Fabric 1.0. As such, it is subject to change and will not be
set in stone until the beta release at the earliest. Additionally, the code and
documentation may at times be out of sync, so please keep this in mind.


About
=====

.. include:: ../README


Installation
=====================

Latest stable version
---------------------

Stable releases of Fabric are best installed via ``easy_install`` or ``pip``;
or you may download TGZ or ZIP source archives from a couple of official
locations. Detailed instructions and links may be found on the
:doc:`installation` page.

Development version
-------------------

We recommend using the stable version of Fabric; releases are made often to
prevent any large gaps in functionality between the latest stable release and
the development version.

However, if you want to live on the edge, you can pull down the latest source
code from our Git repository, or fork us on Github. Please see the
:doc:`development` page for details.


Getting help
============

Mailing list
------------

The best way to get help with using Fabric is via the `fab-user mailing list
<http://lists.nongnu.org/mailman/listinfo/fab-user>`_ (currently hosted at
``nongnu.org``.) The Fabric developers do their best to reply promptly, and the
list contains an active community of other Fabric users and contributors as
well.

Bugs
----

Fabric has no official bug tracker at this point in time, but getting one is
very high on our priority list, so keep an eye out! For the time being, please
submit bug reports via the mailing list (see above) or e-mail the development
team directly at ``developers [at] fabfile [dot] org``.

.. note:: Using the mailing list is preferred -- it increases your chances of
    getting prompt feedback, and also allows other users to confirm your bug
    report and thus give it a higher priority.

Wiki
----

There is an official Fabric wiki reachable at `wiki.fabfile.org
<http://wiki.fabfile.org>`_, although as of this writing its usage patterns
are still being worked out. There is a `TodoList page
<http://wiki.fabfile.org/TodoList>`_ which may also be used to submit bug
reports, as an alternative to sending email.


Documentation
=============

.. toctree::
    :maxdepth: 3

    installation
    development
    usage
    compatibility


API
===

.. toctree::
    :maxdepth: 3
    :glob:

    api/*


Contrib
=======

.. toctree::
    :maxdepth: 3
    :glob:

    contrib/*


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
