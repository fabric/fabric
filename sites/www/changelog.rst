=========
Changelog
=========

.. note::
    Looking for the Fabric 1.x changelog? See :doc:`/changelog-v1`.

- :feature:`1772` ``@hosts`` is back -- as a `@task <fabric.tasks.task>`/`Task
  <fabric.tasks.Task>` parameter of the same name. Acts much like a per-task
  :option:`--hosts`, but can optionally take dicts of `.Connection` kwargs as
  well as the typical shorthand host strings.

  .. note::
    As of this change, we are now recommending the use of the
    new-in-this-release Fabric-level `@task <fabric.tasks.task>`/`Task
    <fabric.tasks.Task>` API members, even if you're not using the ``hosts``
    kwarg -- it will help future-proof your code for similar feature-adds
    later, and just generally be less confusing than having mixed Invoke/Fabric
    imports for these object types.

- :feature:`1766` Reinstate support for use as ``python -m fabric``, which (as
  in v1) now behaves identically to invoking ``fab``. Thanks to
  ``@RupeshPatro`` for the original patchset.
- :bug:`1753` Set one of our test modules to skip user/system SSH config file
  loading by default, as it was too easy to forget to do so for tests aimed at
  related functionality. Reported by Chris Rose.
- :release:`2.1.3 <2018-05-24>`
- :bug:`-` Our packaging metadata lacked a proper ``MANIFEST.in`` and thus some
  distributions were not including ancillary directories like tests and
  documentation. This has been fixed.
- :bug:`-` Our ``packages=`` argument to ``setuptools.setup`` was too specific
  and did not allow for subpackages...such as the newly added
  ``fabric.testing``. Fixed now.
- :release:`2.1.2 <2018-05-24>`
- :bug:`-` Minor fix to ``extras_require`` re: having ``fabric[pytest]``
  encompass the contents of ``fabric[testing]``.
- :release:`2.1.1 <2018-05-24>`
- :bug:`-` Somehow neglected to actually add ``extras_require`` to our
  ``setup.py`` to enable ``pip install fabric[testing]`` et al. This has been
  fixed. We hope.
- :release:`2.1.0 <2018-05-24>`
- :release:`2.0.2 <2018-05-24>`
- :feature:`-` Exposed our previously internal test helpers for use by
  downstream test suites, as the :ref:`fabric.testing <testing-subpackage>`
  subpackage.

  .. note::
    As this code requires non-production dependencies, we've also updated our
    packaging metadata to publish some setuptools "extras", ``fabric[testing]``
    (base) and ``fabric[pytest]`` (for pytest users).

- :support:`1761 backported` Integration tests were never added to Travis or
  ported to pytest before 2.0's release; this has been addressed.
- :support:`1759 backported` Apply the ``black`` code formatter to the codebase
  and engage it on Travis-CI. Thanks to Chris Rose.
- :support:`1745 backported` Wrap any imports of ``invoke.vendor.*`` with
  ``try``/``except`` such that downstream packages which have removed
  ``invoke.vendor`` are still able to function by using stand-alone
  dependencies. Patch courtesy of Othmane Madjoudj.
- :release:`2.0.1 <2018-05-14>`
- :bug:`1740` A Python 3 wheel was not uploaded during the previous release as
  expected; it turned out we were lacking the typical 'build universal wheels'
  setting in our ``setup.cfg`` (due to copying it from the one other project in
  our family of projects which explicitly cannot build universal wheels!) This
  has been fixed and a proper universal wheel is now built.
- :release:`2.0.0 <2018-05-08>`
- :feature:`-` Rewrite for 2.0! See :ref:`upgrading`.
