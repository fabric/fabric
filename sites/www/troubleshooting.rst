===============
Troubleshooting
===============

Stuck? Having a problem? Here are the steps to try before you submit a bug
report.

* **Make sure you're on the latest version.** If you're not on the most recent
  version, your problem may have been solved already! Upgrading is always the
  best first step.
* **Try older versions.** If you're already *on* the latest Fabric, try rolling
  back a few minor versions (e.g. if on 2.3, try Fabric 2.2 or 2.1) and see if
  the problem goes away. This will help the devs narrow down when the problem
  first arose in the commit log.
* **Try switching up your Paramiko.** Fabric relies heavily on the Paramiko
  library for its SSH functionality, so try applying the above two steps to
  your Paramiko install as well.

  .. note::
      Fabric versions sometimes have different Paramiko dependencies - so to
      try older Paramikos you may need to downgrade Fabric as well.

* **Make sure Fabric is really the problem.** If your problem is in the
  behavior or output of a remote command, try recreating it without Fabric
  involved:

    * Find out the exact command Fabric is executing on your behalf:

        - In 2.x and up, activate command echoing via the ``echo=True`` keyword
          argument, the ``run.echo`` config setting, or the ``-e`` CLI option.
        - In 1.x, run Fabric with ``--show=debug`` and look for ``run:`` or
          ``sudo:`` lines.

    * Execute the command in an interactive remote shell first, to make sure it
      works for a regular human; this will catch issues such as errors in
      command construction.
    * If that doesn't find the issue, run the command over a non-shell SSH
      session, e.g. ``ssh yourserver "your command"``. Depending on your
      settings and Fabric version, you may want to use ``ssh -T`` (disable PTY)
      or ``-t`` (enable PTY) to most closely match how Fabric is executing the
      command.

* **Enable Paramiko-level debug logging.** If your issue is in the lower level
  Paramiko library, it can help us to see the debug output Paramiko prints. At
  top level in your fabfile (or in an appropriate module, if not using a
  fabfile), add the following::

      import logging
      logging.basicConfig(level=logging.DEBUG)

  This should start printing Paramiko's debug statements to your standard error
  stream. (Feel free to add more logging kwargs to ``basicConfig()`` such as
  ``filename='/path/to/a/file'`` if you like.)

  Then submit this info to anybody helping you on IRC or in your bug report.
