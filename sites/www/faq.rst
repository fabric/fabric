=========================================
Frequently Asked/Answered Questions (FAQ)
=========================================

These are some of the most commonly encountered problems or frequently asked
questions which we receive from users. They aren't intended as a substitute for
reading the rest of the documentation, so please make sure you check it out if
your question is not answered here.

.. note::
    Most API examples and links are for version 2 and up; FAQs specific to
    version 1 will typically be marked as such.

.. warning::
    Many questions about shell command execution and task behavior are answered
    on `Invoke's FAQ page <http://www.pyinvoke.org/faq.html>`_ - please check
    there also!


.. _remote-env-vars-dont-work:

Explicitly set env variables are not being set correctly on the remote end!
===========================================================================

If your attempts to set environment variables for things like `Connection.run
<fabric.connection.Connection.run>` appear to silently fail, you're almost
certainly talking to an SSH server which is setting a highly restrictive
`AcceptEnv <https://man.openbsd.org/sshd_config#AcceptEnv>`_.

To fix, you can either modify the server's configuration to allow the env vars
you're setting, or use the ``inline_ssh_env`` `~fabric.connection.Connection`
parameter (or the :ref:`global config option <default-values>` of the same
name) to force Fabric to send env vars prefixed before your command strings
instead.


The remote shell environment doesn't match interactive shells!
==============================================================

You may find environment variables (or the behavior they trigger) differ
interactively vs scripted via Fabric. For example, a program that's on your
``$PATH`` when you manually ``ssh`` in might not be visible when using
`Connection.run <fabric.connection.Connection.run>`; or special per-program env
vars such as those for Python, pip, Java etc are not taking effect; etc.

The root cause of this is typically because the SSH server runs non-interactive
commands via a very limited shell call: ``/path/to/shell -c "command"`` (for
example, `OpenSSH
<https://github.com/fabric/fabric/issues/1519#issuecomment-411247228>`_). Most
shells, when run this way, are not considered to be either **interactive** or
**login** shells; and this then impacts which startup files get loaded.

Users typically only modify shell files related to interactive operation (such
as ``~/.bash_profile`` or ``/etc/zshrc``); such changes do not take effect when
the SSH server is running one-off commands.

To work around this, consult your shell's documentation to see if it offers any
non-login, non-interactive config files; for example, ``zsh`` lets you
configure ``/etc/zshrc`` or ``~/.zshenv`` for this purpose.

.. note::
    ``bash`` does not appear to offer standard non-login/non-interactive
    startup files, even in version 4. However, it may attempt to determine if
    it's being run by a remote-execution daemon and will apparently source
    ``~/.bashrc`` if so; check to see if this is the case on your target
    systems.

.. note::
    Another workaround for ``bash`` users is to reply on its ``$BASH_ENV``
    functionality, which names a file path as the startup file to load:

    - configure your SSH server to ``AcceptEnv BASH_ENV``, so that you can
      actually set that env var for the remote session at the top level (most
      SSH servers disallow this method by default).
    - decide which file this should be, though if you're already modifying
      files like ``~/.bash_profile`` or ``~/.bashrc``, you may want to just
      point at that exact path.
    - set the Fabric configuration value ``run.env`` to aim at the above path,
      e.g. ``{"BASH_ENV": "~/.bash_profile"}``.


.. _one-shell-per-command:

My (``cd``/``workon``/``export``/etc) calls don't seem to work!
===============================================================

While Fabric can be used for many shell-script-like tasks, there's a slightly
unintuitive catch: each `~fabric.connection.Connection.run` or
`~fabric.connection.Connection.sudo` call (or the ``run``/``sudo`` functions in
v1) has its own distinct shell session. This is required in order for Fabric to
reliably figure out, after your command has run, what its standard out/error
and return codes were.

Unfortunately, it means that code like the following doesn't behave as you
might assume::

    @task
    def deploy(c):
        c.run("cd /path/to/application")
        c.run("./update.sh")

If that were a shell script, the second `~fabric.connection.Connection.run`
call would have executed with a current working directory of
``/path/to/application/`` -- but because both commands are run in their own
distinct session over SSH, it actually tries to execute ``$HOME/update.sh``
instead (since your remote home directory is the default working directory).

A simple workaround is to make use of shell logic operations such as ``&&``,
which link multiple expressions together (provided the left hand side executed
without error) like so::

    def deploy(c):
        c.run("cd /path/to/application && ./update.sh")

.. TODO: reinsert mention of 'with cd():' if that is reimplemented

.. note::
    You might also get away with an absolute path and skip directory changing
    altogether::

        def deploy(c):
            c.run("/path/to/application/update.sh")

    However, this requires that the command in question makes no assumptions
    about your current working directory!


.. TODO:
    reinstate FAQ about 'su' / running as another user, when sudo grows that
    back. (Probably in Invoke tho.)


Why do I sometimes see ``err: stdin: is not a tty``?
====================================================

See :ref:`Invoke's FAQ <stdin-not-tty>` for this; even for Fabric v1,
which is not based on Invoke, the answer is the same.


.. _faq-daemonize:

Why can't I run programs in the background with ``&``? It makes Fabric hang.
============================================================================

Because SSH executes a new shell session on the remote end for each invocation
of ``run`` or ``sudo`` (:ref:`see also <one-shell-per-command>`), backgrounded
processes may prevent the calling shell from exiting until the processes stop
running, which in turn prevents Fabric from continuing on with its own
execution.

The key to fixing this is to ensure that your process' standard pipes are all
disassociated from the calling shell, which may be done in a number of ways
(listed in order of robustness):

* Use a pre-existing daemonization technique if one exists for the program at
  hand -- for example, calling an init script instead of directly invoking a
  server binary.

    * Or leverage a process manager such as ``supervisord``, ``upstart`` or
      ``systemd`` - such tools let you define what it means to "run" one of
      your background processes, then issue init-script-like
      start/stop/restart/status commands. They offer many advantages over
      classic init scripts as well.

* Use ``tmux``, ``screen`` or ``dtach`` to fully detach the process from the
  running shell; these tools have the benefit of allowing you to reattach to
  the process later on if needed (though they are more ad-hoc than
  ``supervisord``-like tools).
* Run the program under ``nohup`` or similar "in-shell" tools - note that this
  approach has seen limited success for most users.


I'm sometimes incorrectly asked for a passphrase instead of a password.
=======================================================================

Due to a bug of sorts in our SSH layer, it's not currently possible for Fabric
to always accurately detect the type of authentication needed. We have to try
and guess whether we're being asked for a private key passphrase or a remote
server password, and in some cases our guess ends up being wrong.

The most common such situation is where you, the local user, appear to have an
SSH keychain agent running, but the remote server is not able to honor your SSH
key, e.g. you haven't yet transferred the public key over or are using an
incorrect username. In this situation, Fabric will prompt you with "Please
enter passphrase for private key", but the text you enter is actually being
sent to the remote end's password authentication.

We hope to address this in future releases by contributing to the
aforementioned SSH library.
