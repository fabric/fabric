===========
Development
===========

The Fabric development team consists of two programmers, `Jeff Forcier
<http://bitprophet.org>`_ and `Christian Vest Hansen
<http://my.opera.com/karmazilla/blog/>`_, with Jeff taking the lead role.
However, dozens of other developers pitch in by submitting patches and ideas,
via individual emails, `Redmine <http://code.fabfile.org>`_, the `mailing list
<http://lists.nongnu.org/mailman/listinfo/fab-user>`_ and `GitHub <http://github.com/bitprophet/fabric>`_.

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
  `ticket tracker <http://code.fabfile.org>`_ first, though, when submitting
  feature ideas.)
* **Report bugs.** Pretty much a special case of the previous item: if you
  think you've found a bug in Fabric, check on the `Redmine ticket tracker
  <http://code.fabfile.org>`_ to see if anyone's reported it yet, and if not --
  file a bug! If possible, try to make sure you can replicate it repeatedly,
  and let us know the circumstances (what version of Fabric you're using, what
  platform you're on, and what exactly you were doing when the bug cropped up.)
* **Submit patches or new features.** See the :ref:`source-code-checkouts`
  documentation, grab a Git clone of the source, and either email a patch to
  the mailing list or make your own GitHub fork and post a link to your fork
  (or a specific commit on a fork) in the appropriate Redmine ticket.
  While we may not always reply promptly, we do try to make time eventually to
  inspect all contributions and either incorporate them or explain why we don't
  feel the change is a good fit.

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

  * At time of writing, this means that Fabric maintains an ``0.9`` release
    branch, from which all prerelease and final release versions of 0.9.x, e.g.
    0.9rc1 and 0.9.0 and so forth, are cut.
  * New features intended for the next major release (Fabric 1.0) will be kept
    in the ``master`` branch. Once the 1.0 alpha or beta period begins, this
    work will be split off into a ``1.0`` branch and ``master`` will start
    forming Fabric 1.1.
  * While we try our best not to commit broken code or change APIs without
    warning, as with many other open-source projects we can only have a
    guarantee of stability in the release branches. Only follow ``master`` if
    you're willing to deal with a little pain.
  * Conversely, because we try to keep release branches relatively stable, you
    may find it easier to use Fabric from a source checkout of a release branch
    instead of upgrading to new released versions. This can provide a decent
    middle ground between stability and the ability to get bugfixes or
    backported features easily.

* The core developers will take care of performing merging/branching on the
  official repositories. Since Git is Git, contributors may of course do
  whatever they wish in their own clones/forks.
* Bugfixes are to be performed on release branches and then merged into
  ``master`` so that ``master`` is always up-to-date (or nearly so; while it's
  not mandatory to merge after every bugfix, doing so at least daily is a good
  idea.)
* Feature branches, if used, should periodically merge in changes from
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

For example, the upcoming 1.0 will mean that we feel Fabric has reached its
primary design goals of a solid core API and well-defined area for additional
functionality to live. Version 2.0 might, for example, indicate a rewrite using
a new underlying network technology (though this isn't necessarily planned.)

Major releases will often be backwards-incompatible with the previous line of
development, though this is not a requirement, just a usual happenstance.
Users should expect to have to make at least some changes to their fabfiles
when switching between major versions.

Minor
-----

Minor releases, such as moving from 1.0 to 1.1, typically mean that a new,
large feature has been added. They are also sometimes used to mark off the
fact that a lot of bug fixes or small feature modifications have occurred
since the previous minor release. (And, naturally, some of them will involve
both at the same time.)

These releases are guaranteed to be backwards-compatible with all other
releases containing the same major version number, so a fabfile that works
with 1.0 should also work fine with 1.1 or even 1.9.

.. note::

    This policy marks a departure from early versions of Fabric, wherein the
    minor release number was the backwards-compatibility boundary -- e.g.
    Fabric 0.1 was incompatible with Fabric 0.0.x.

    Fabric 0.1 to 0.9 also marked a rewrite of the software and a change of
    hands, and so did break backwards compatibility. This will not happen
    again.

Bugfix/tertiary
---------------

The third and final part of version numbers, such as the '3' in 1.0.3,
generally indicate a release containing one or more bugfixes, although minor
feature additions or modifications may sometimes occur.

This third number is sometimes omitted for the first major or minor release in
a series, e.g. 1.2 or 2.0, and in these cases it can be considered an implicit
zero (e.g. 2.0.0).

.. note::

    The 0.9.x branch of development will see more significant feature additions
    than is planned for future lines. This is in order to backport some useful
    features from the 1.0 branch so that the feature gap between 0.9 and 1.0 is
    not as large as it was when 0.9.0 was released.

    In 1.0.x and so forth, tertiary releases are more likely to contain just
    bugfixes or tweaks, and not new functionality, as the window between minor
    releases is expected to be shorter than that of 0.1 => 0.9.


Support of older releases
=========================

Major and minor releases do not mark the end of the previous line or lines of
development:

* The two most recent stable release branches will continue to receive critical
  bugfixes. For example, once 1.0 is released, both it and 0.9 will likely see
  tertiary releases until 1.1 is released, at which point only 1.1 and 1.0 will
  get bugfixes.
* Depending on the nature of bugs found and the difficulty in backporting them,
  older release lines may also continue to get bugfixes -- but there's no
  longer a guarantee of any kind. Thus, if a bug is found in 1.1 that affects
  0.9 and can be easily applied, we *may* cut a new 0.9.x release.
* This policy may change in the future to accomodate more branches, depending
  on development speed.

We hope that this policy will allow us to have a rapid minor release cycle (and
thus keep new features coming out frequently) without causing users to feel too
much pressure to upgrade right away. At the same time, the backwards
compatibility guarantee means that users should still feel comfortable
upgrading to the next minor release in order to stay within this sliding
support window.
