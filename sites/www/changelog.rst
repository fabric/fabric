=========
Changelog
=========

.. note::
    Looking for the Fabric 1.x changelog? See :doc:`/changelog-v1`.

- :release:`2.0.3 <2018-07-13>`
- :bug:`1753` Set one of our test modules to skip user/system SSH config file
  loading by default, as it was too easy to forget to do so for tests aimed at
  related functionality. Reported by Chris Rose.
- :bug:`-` Our packaging metadata lacked a proper ``MANIFEST.in`` and thus some
  distributions were not including ancillary directories like tests and
  documentation. This has been fixed.
- :release:`2.0.2 <2018-05-24>`
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
