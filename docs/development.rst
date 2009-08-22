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
  think you've found a bug in Fabric, check on the `ticket tracker
  <http://code.fabfile.org>`_ to see if anyone's reported it yet, and if not --
  file a bug! If possible, try to make sure you can replicate it repeatedly,
  and let us know the circumstances (what version of Fabric you're using, what
  platform you're on, and what exactly you were doing when the bug cropped up.)
* **Submit patches or new features.** See the :ref:`source-code-checkouts`
  documentation, grab a Git clone of the source, and either email a patch to
  the mailing list or make your own GitHub fork and send us a pull request.
  While we may not always reply promptly, we do try to make time eventually to
  inspect all contributions and either incorporate them or explain why we don't
  feel the change is a good fit.

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
    branch, from which the 0.9 betas are cut, and from which the final release
    and bugfix releases will continue to be generated from.
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
1.2-beta1. Each release will be marked as a tag in the Git repositories, and
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
since the previous minor release.

These releases are guaranteed to be backwards-compatible with all other
releases containing the same major version number, so a fabfile that works
with 1.0 should also work fine with 1.1 or even 1.9.

.. note::

    This policy marks a departure from early versions of Fabric, wherein the
    minor release number was the backwards-compatibility boundary -- e.g.
    Fabric 0.1 was incompatible with Fabric 0.0.x.

Bugfix/tertiary
---------------

The third and final part of version numbers, such as the '3' in 1.0.3,
generally indicate a release containing one or more bugfixes, although minor
feature additions or modifications are also common.

This third number is sometimes omitted for the first major or minor release in
a series, e.g. 1.2 or 2.0, and in these cases it can be considered an implicit
zero (e.g. 2.0.0). Fabric will likely include the explicit zero in these cases,
however -- after all, explicit is better than implicit.
