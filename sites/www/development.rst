===========
Development
===========

The Fabric development team is headed by `Jeff Forcier
<http://bitprophet.org>`_, aka ``bitprophet``.  However, dozens of other
developers pitch in by submitting patches and ideas via `GitHub issues and pull
requests <https://github.com/fabric/fabric>`_, :ref:`IRC <irc>` or the `mailing
list <http://lists.nongnu.org/mailman/listinfo/fab-user>`_.

Get the code
============

Please see the :ref:`source-code-checkouts` section of the :doc:`installing`
page for details on how to obtain Fabric's source code.

Contributing
============

There are a number of ways to get involved with Fabric:

* **Use Fabric and send us feedback!** This is both the easiest and arguably
  the most important way to improve the project -- let us know how you
  currently use Fabric and how you want to use it. (Please do try to search the
  `ticket tracker`_ first, though,
  when submitting feature ideas.)
* **Report bugs or submit feature requests.** We follow `contribution-guide.org`_'s guidelines, so please check them out before
  visiting the `ticket tracker`_.
* **Fix bugs or implement features!** Again, follow `contribution-guide.org`_
  for details on this process. Regarding the changelog step, our changelog is
  stored in ``sites/www/changelog.rst``.

.. _contribution-guide.org: http://contribution-guide.org
.. _ticket tracker: https://github.com/fabric/fabric/issues

While we may not always reply promptly, we do try to make time eventually to
inspect all contributions and either incorporate them or explain why we don't
feel the change is a good fit.


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
