=========================
Upgrading from Fabric 1.x
=========================

* Host strings are now Connection objects
* Roles (and other lists-of-host-strings such as the result of using ``-H`` on
  the CLI) are now Group objects
* There is no more built-in "use shell" or "shell" option - if your remote sshd
  isn't wrapping commands in a shell execution (most of them do) use the new
  command processing framework to add your own to taste.
