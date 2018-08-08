=========
Changelog
=========

.. note::
    Looking for the Fabric 1.x changelog? See :doc:`/changelog-v1`.

- :feature:`1826` Add a new Boolean configuration and
  `~fabric.connection.Connection` parameter, ``inline_ssh_env``, which (when
  set to ``True``) changes how Fabric submits shell environment variables to
  remote servers; this feature helps work around commonly restrictive
  ``AcceptEnv`` settings on SSH servers. Thanks to Massimiliano Torromeo and
  Max Arnold for the reports.
- :release:`2.2.2 <2018-07-31>`
- :release:`2.1.5 <2018-07-31>`
- :release:`2.0.4 <2018-07-31>`
- :bug:`-` Implement ``__lt__`` on `~fabric.connection.Connection` so it can be
  sorted; this was overlooked when implementing things like ``__eq__`` and
  ``__hash__``. (No, sorting doesn't usually matter much for this object type,
  but when you gotta, you gotta...)
- :support:`1819 backported` Moved example code from the README into the Sphinx
  landing page so that we could apply doctests; includes a bunch of corrections
  to invalid example code! Thanks to Antonio Feitosa for the initial catch &
  patch.
- :bug:`1749` Improve `~fabric.transfer.Transfer.put` behavior when uploading
  to directory (vs file) paths, which was documented as working but had not
  been fully implemented. The local path's basename (or file-like objects'
  ``.name`` attribute) is now appended to the remote path in this case. Thanks
  to Peter Uhnak for the report.
- :feature:`1831` Grant `~fabric.group.Group` (and subclasses) the ability to
  take arbitrary keyword arguments and pass them onto the internal
  `~fabric.connection.Connection` constructors. This allows code such as::

    mygroup = Group('host1', 'host2', 'host3', user='admin')

  which was previously impossible without manually stuffing premade
  ``Connection`` objects into `Group.from_connections
  <fabric.group.Group.from_connections>`.
- :bug:`1762` Fix problem where lower configuration levels' setting of
  ``connect_kwargs.key_filename`` were being overwritten by the CLI
  ``--identity`` flag's value...even when that value was the empty list.
  CLI-given values are supposed to win, but not quite that hard. Reported by
  ``@garu57``.
- :support:`1653 backported` Clarify `~fabric.transfer.Transfer` API docs
  surrounding remote file paths, such as the lack of tilde expansion (a buggy
  and ultimately unnecessary v1 feature). Thanks to ``@pint12`` for bringing it
  up.
- :release:`2.2.1 <2018-07-18>`
- :bug:`1824` The changes implementing :issue:`1772` failed to properly account
  for backwards compatibility with Invoke-level task objects. This has been
  fixed; thanks to ``@ilovezfs`` and others for the report.
- :release:`2.2.0 <2018-07-13>`
- :release:`2.1.4 <2018-07-13>`
- :release:`2.0.3 <2018-07-13>`
- :bug:`-` The `fabric.testing.fixtures.remote` pytest fixture was found to not
  be properly executing expectation/sanity tests on teardown; this was an
  oversight and has been fixed.
- :support:`-` Updated the minimum required Invoke version to ``1.1``.
- :feature:`1772` ``@hosts`` is back -- as a `@task <fabric.tasks.task>`/`Task
  <fabric.tasks.Task>` parameter of the same name. Acts much like a per-task
  :option:`--hosts`, but can optionally take dicts of
  `fabric.connection.Connection` kwargs as well as the typical shorthand host
  strings.

  .. note::
    As of this change, we are now recommending the use of the
    new-in-this-release Fabric-level `@task <fabric.tasks.task>`/`Task
    <fabric.tasks.Task>` objects instead of their Invoke counterparts, even if
    you're not using the ``hosts`` kwarg -- it will help future-proof your code
    for similar feature-adds later, and generally be less confusing than having
    mixed Invoke/Fabric imports for these object types.

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
