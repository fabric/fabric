=========================
Upgrading from Fabric 1.x
=========================

.. TODO: break into sections, etc

* Host strings are now Connection objects
* Roles (and other lists-of-host-strings such as the result of using ``-H`` on
  the CLI) are now Group objects
* There is no more built-in "use shell" or "shell" option - if your remote sshd
  isn't wrapping commands in a shell execution (most of them do) use the new
  command processing framework to add your own to taste.
* Top-level "operations" functions like ``run``, ``local``, ``put`` and so
  forth, are now methods on ``Connection`` objects.
* Old-style task functions (those not decorated with ``@task``) are gone. You
  must now always use ``@task``.
* ``fabric.api`` is gone; all useful imports are now available at the top
  level, e.g. ``from fabric import Connection``.
* ``fabric.env`` is gone; there is no more global state, only
  per-task-invocation ``Connection`` objects handed to your tasks by the CLI
  and execution machinery:
  
    * "Config options" that used to exist as attributes/keys on ``env`` are now
      part of read-only ``invoke.Configuration`` objects living inside of the
      ``Connection`` objects your tasks receive.
    * "Per-session" values such as ``env.hosts`` are now mostly present as
      read-only, informational attributes on ``Connection.session``.

.. TODO:
    how to perform "setup" or "pre-execution" things like dynamically setting a
    "host list", where 'fab foo bar' wants 'foo' to change 'bar's context
    somehow? (Especially, what about 'fab foo bar biz baz' - can't simply tell
    'foo' to run 'bar' with some hardcoded params or anything.)
