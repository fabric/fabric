=========
Changelog
=========

.. note::
    Looking for the Fabric 1.x changelog? See :doc:`/changelog-v1`.

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
