===========
Development
===========

The Fabric development team is headed by `Jeff Forcier
<http://bitprophet.org>`_, aka ``bitprophet``.  However, dozens of other
developers pitch in by submitting patches and ideas via `GitHub
<https://github.com/fabric/fabric>`_, :ref:`IRC <irc>` or the `mailing list
<http://lists.nongnu.org/mailman/listinfo/fab-user>`_.

Get the code
============

Please see the :ref:`source-code-checkouts` section of the :doc:`installation`
page for details on how to obtain Fabric's source code.

Contributing
============

There are a number of ways to get involved with Fabric:

* **Use Fabric and send us feedback!** This is both the easiest and arguably
  the most important way to improve the project -- let us know how you
  currently use Fabric and how you want to use it. (Please do try to search the
  `ticket tracker <https://github.com/fabric/fabric/issues>`_ first, though,
  when submitting feature ideas.)
* **Report bugs.** Pretty much a special case of the previous item: if you
  think you've found a bug in Fabric, check on the `ticket tracker
  <https://github.com/fabric/fabric/issues>`_ to see if anyone's reported it
  yet, and if not -- file a bug! If possible, try to make sure you can
  replicate it repeatedly, and let us know the circumstances (what version of
  Fabric you're using, what platform you're on, and what exactly you were doing
  when the bug cropped up.)
* **Submit patches or new features.** Make a `Github <https://github.com>`_
  account, `create a fork <http://help.github.com/fork-a-repo/>`_ of `the main
  Fabric repository <https://github.com/fabric/fabric>`_, and `submit a pull
  request <http://help.github.com/send-pull-requests/>`_.

While we may not always reply promptly, we do try to make time eventually to inspect all contributions and either incorporate them or explain why we don't feel the change is a good fit.

Communication
-------------

If a ticket-tracker ticket exists for a given issue, **please** keep all
communication in that ticket's comments -- for example, when submitting patches
via Github, it's easier for us if you leave a note in the ticket **instead of**
sending a Github pull request.

The core devs receive emails for just about any ticket-tracker activity, so
additional notices via Github or other means only serve to slow things down.

Style
-----

Fabric tries hard to honor `PEP-8`_, especially (but not limited to!) the
following:

* Keep all lines under 80 characters. This goes for the ReST documentation as
  well as code itself.

  * Exceptions are made for situations where breaking a long string (such as a
    string being ``print``-ed from source code, or an especially long URL link
    in documentation) would be kind of a pain.

* Typical Python 4-space (soft-tab) indents. No tabs! No 8 space indents! (No
  2- or 3-space indents, for that matter!)
* ``CamelCase`` class names, but ``lowercase_underscore_separated`` everything
  else.

.. _PEP-8: http://www.python.org/dev/peps/pep-0008/

Branching/Repository Layout
===========================

While Fabric's development methodology isn't set in stone yet, the following
items detail how we currently organize the Git repository and expect to perform
merges and so forth. This will be chiefly of interest to those who wish to
follow a specific Git branch instead of released versions, or to any
contributors.

* We use a combined 'release and feature branches' methodology, where every
  minor release (e.g. 0.9, 1.0, 1.1, 1.2 etc; see :ref:`releases` below for
  details on versioning) gets a release branch for bugfixes, and big feature
  development is performed in a central ``master`` branch and/or in
  feature-specific feature branches (e.g. a branch for reworking the internals
  to be threadsafe, or one for overhauling task dependencies, etc.)
* Releases each get their own release branch, e.g. ``0.9``, ``1.0``, ``1.1``
  etc, and from these the actual releases are tagged, e.g. ``0.9.3`` or
  ``1.0.0``.
* New feature work is typically done in feature branches, whose naming
  convention is ``<ticket number>-<short-description>``. For example, ticket
  #61, which concerned adding ``cd`` support to ``get`` and ``put``, was
  developed in a branch named ``61-add-cd-to-get-put``.

  * These branches are not intended for public use, and may be cleaned out of
    the repositories periodically. Ideally, no one feature will be in
    development long enough for its branch to become used in production!

* Completed feature work is merged into the ``master`` branch, and once enough
  new features are done, a new release branch is created and optionally used to
  create prerelease versions for testing -- or simply released as-is.
* While we try our best not to commit broken code or change APIs without
  warning, as with many other open-source projects we can only have a guarantee
  of stability in the release branches. Only follow ``master`` (or, even worse,
  feature branches!) if you're willing to deal with a little pain.
* Conversely, because we try to keep release branches relatively stable, you
  may find it easier to use Fabric from a source checkout of a release branch
  instead of manually upgrading to new released versions. This can provide a
  decent middle ground between stability and the ability to get bugfixes or
  backported features easily.
* The core developers will take care of performing merging/branching on the
  official repositories. Since Git is Git, contributors may of course do
  whatever they wish in their own clones/forks.
* Bugfixes are to be performed on release branches and then merged into
  ``master`` so that ``master`` is always up-to-date (or nearly so; while it's
  not mandatory to merge after every bugfix, doing so at least daily is a good
  idea.)
* Feature branches should periodically merge in changes from
  ``master`` so that when it comes time for them to merge back into ``master``
  things aren't quite as painful.

.. _releases:

Releases
========

Fabric tries to follow open-source standards and conventions in its release
tagging, including typical version numbers such as 2.0, 1.2.5, or
1.2b1. Each release will be marked as a tag in the Git repositories, and
are broken down as follows:

Major
-----

Major releases update the first number, e.g. going from 0.9 to 1.0, and
indicate that the software has reached some very large milestone.

For example, the 1.0 release signified a commitment to a medium to long term
API and some significant backwards incompatible (compared to the 0.9 series)
features. Version 2.0 might indicate a rewrite using a new underlying network
technology or an overhaul to be more object-oriented.

Major releases will often be backwards-incompatible with the previous line of
development, though this is not a requirement, just a usual happenstance.
Users should expect to have to make at least some changes to their fabfiles
when switching between major versions.

Minor
-----

Minor releases, such as moving from 1.0 to 1.1, typically mean that one or more
new, large features has been added. They are also sometimes used to mark off
the fact that a lot of bug fixes or small feature modifications have occurred
since the previous minor release. (And, naturally, some of them will involve
both at the same time.)

These releases are guaranteed to be backwards-compatible with all other
releases containing the same major version number, so a fabfile that works
with 1.0 should also work fine with 1.1 or even 1.9.

Bugfix/tertiary
---------------

The third and final part of version numbers, such as the '3' in 1.0.3,
generally indicate a release containing one or more bugfixes, although minor
feature modifications may (rarely) occur.

This third number is sometimes omitted for the first major or minor release in
a series, e.g. 1.2 or 2.0, and in these cases it can be considered an implicit
zero (e.g. 2.0.0).

.. note::

    The 0.9 series of development included more significant feature work than
    is typically found in tertiary releases; from 1.0 onwards a more
    traditional approach, as per the above, is used.


Support of older releases
=========================

Major and minor releases do not mark the end of the previous line or lines of
development:

* The two most recent minor release branches will continue to receive critical
  bugfixes. For example, if 1.1 were the latest minor release, it and 1.0 would
  get bugfixes, but not 0.9 or earlier; and once 1.2 came out, this window
  would then only extend back to 1.1.
* Depending on the nature of bugs found and the difficulty in backporting them,
  older release lines may also continue to get bugfixes -- but there's no
  longer a guarantee of any kind. Thus, if a bug were found in 1.1 that
  affected 0.9 and could be easily applied, a new 0.9.x version *might* be
  released.
* This policy may change in the future to accommodate more branches, depending
  on development speed.

We hope that this policy will allow us to have a rapid minor release cycle (and
thus keep new features coming out frequently) without causing users to feel too
much pressure to upgrade right away. At the same time, the backwards
compatibility guarantee means that users should still feel comfortable
upgrading to the next minor release in order to stay within this sliding
support window.
