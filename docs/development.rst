===========
Development
===========

The Fabric development team consists of two programmers, `Jeff Forcier
<http://bitprophet.org>`_ and `Christian Vest Hansen
<http://my.opera.com/karmazilla/blog/>`_, with Jeff taking the lead role.
However, dozens of other developers pitch in by submitting patches and ideas,
via individual emails, the `mailing list
<http://lists.nongnu.org/mailman/listinfo/fab-user>`_, and the community coding
site `GitHub <http://github.com/bitprophet/fabric>`_.

Get the code
============

Please see the :ref:`source-code-checkouts` section of the :doc:`installation`
page for details on how to obtain Fabric's source code.

Contributing
============

TODO: expand on these :)

* Best: fork on Github, hack, send pull request, try not to feel hurt when
  patch is tweaked by anal-retentive core dev :D
* Good: git clone without forking on Github, email patch to mailing list or
  ``developers [at] fabfile [dot] org``
* Still really useful: email feedback to mailing list or developers

Branches
========

TODO: expand on this

* Development methodology is still being settled on and is not necessarily set
  in stone.
* Lead devs take care of doing merging/branching on the official repos (since
  Git is Git, contributors may of  course do whatever they wish in their own
  clones/forks.)
* We use a combined 'release and feature branches' methodology, where every
  minor release (see below) gets a release branch for bugfixes, and big
  feature development is performed in a central 'master' branch and/or in
  feature-specific feature branches.

  * Note to folks following the 0.9 alpha/beta: this won't actually be set up
    till 0.9-final goes out the door :)
* Bugfixes are to be performed on release branches and then immediately
  backported to the master branch, so that the master branch is always
  up-to-date.
* Feature branches should periodically merge in changes from master so that
  when it comes time for them to merge back in, things aren't quite as
  painful.

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
functionality to live. Version 2.0 might indicate a rewrite using a new
underlying network technology (though this isn't necessarily planned :)).

Major releases will often be backwards-incompatible with the previous line of
development, though this is not a requirement, just a usual happenstance.
Users should expect to have to make at least some changes to their fabfiles
when switching major versions.

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
    minor release number was the backwards-compatibility boundary.

Bugfix/tertiary
---------------

The third and final part of version numbers, such as the '3' in 1.0.3,
generally indicate a release containing one or more bugfixes, although minor
feature additions or modifications are also common.

This third number is sometimes omitted for the first major or minor release in
a series, e.g. 1.2 or 2.0, and in these cases it can be considered an implicit
zero (e.g. 2.0.0).
