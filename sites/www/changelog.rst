=========
Changelog
=========

.. note::
    Looking for the Fabric 1.x changelog? See :doc:`/changelog-v1`.

- :release:`2.0.5 <2018-09-13>`
- :bug:`-` Fix a bug preventing tab completion (using the Invoke-level
  ``--complete`` flag) from completing task names correctly (behavior was to
  act as if there were never any tasks present, even if there was a valid
  fabfile nearby).
- :bug:`1850` Skip over ``ProxyJump`` configuration directives in SSH config
  data when they would cause self-referential ``RecursionError`` (e.g. due to
  wildcard-using ``Host`` stanzas which include the jump server itself).
  Reported by Chris Adams.
- :bug:`-` Some debug logging was reusing Invoke's logger object, generating
  log messages "named" after ``invoke`` instead of ``fabric``. This has been
  fixed by using Fabric's own logger everywhere instead.
- :bug:`1852` Grant internal `~fabric.connection.Connection` objects created
  during ``ProxyJump`` based gateways/proxies a copy of the outer
  ``Connection``'s configuration object. This was not previously done, which
  among other things meant one could not fully disable SSH config file loading
  (as the internal ``Connection`` objects would revert to the default
  behavior). Thanks to Chris Adams for the report.
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
- :bug:`1762` Fix problem where lower configuration levels' setting of
  ``connect_kwargs.key_filename`` were being overwritten by the CLI
  ``--identity`` flag's value...even when that value was the empty list.
  CLI-given values are supposed to win, but not quite that hard. Reported by
  ``@garu57``.
- :support:`1653 backported` Clarify `~fabric.transfer.Transfer` API docs
  surrounding remote file paths, such as the lack of tilde expansion (a buggy
  and ultimately unnecessary v1 feature). Thanks to ``@pint12`` for bringing it
  up.
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
