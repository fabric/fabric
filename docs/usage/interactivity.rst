================================
Interaction with remote programs
================================

Fabric's primary operations, `~fabric.operations.run` and
`~fabric.operations.sudo`, are capable of sending local input to the remote
end, in a manner nearly identical to the ``ssh`` program. For example, programs
which display password prompts (e.g. a database dump utility, or changing a
user's password) will behave just as if you were interacting with them
directly.

However, as with ``ssh`` itself, Fabric's implementation of this feature is
subject to a handful of limitations which are not always intuitive. This
document discusses such issues in detail.

.. note::
    Readers unfamiliar with the basics of Unix stdout and stderr pipes, and/or
    terminal devices, may wish to visit the Wikipedia pages for `Unix pipelines
    <http://en.wikipedia.org/wiki/Pipe_(Unix)>`_ and `Pseudo terminals
    <http://en.wikipedia.org/wiki/Pseudo_terminal>`_ respectively.


.. _combine_streams:

Combining stdout and stderr
===========================

The first issue to be aware of is that of the stdout and stderr streams, and
why they are separated or combined as needed.

Buffering
---------

Fabric 0.9.x and earlier, and Python itself, buffer output on a line-by-line
basis: text is not printed to the user until a newline character is found.
This works fine in most situations but becomes problematic when one needs to
deal with partial-line output such as prompts.

.. note::
    Line-buffered output can make programs appear to halt or freeze for no
    reason, as prompts print out text without a newline, waiting for the user
    to enter their input and press Return.

Newer Fabric versions buffer both input and output on a character-by-character
basis in order to make interaction with prompts possible. This has the
convenient side effect of enabling interaction with complex programs utilizing
the "curses" libraries or which otherwise redraw the screen (think ``top``).

Crossing the streams
--------------------

Unfortunately, printing to stderr and stdout simultaneously (as many programs
do) means that when the two streams are printed independently one byte at a
time, they can become garbled or meshed together. While this can sometimes be
mitigated by line-buffering one of the streams and not the other, it's still a
serious issue.

To solve this problem, Fabric uses a Paramiko setting that merges the two
streams at a low level and causes output to appear more naturally. This setting
is represented in Fabric as the :ref:`combine-stderr` env var and keyword
argument, and is ``True`` by default.

Due to this default setting, output will appear correctly, but at the
cost of an empty ``.stderr`` attribute on the return values of
`~fabric.operations.run`/`~fabric.operations.sudo`, as all output will appear
to be stdout.

Conversely, users requiring a distinct stderr stream at the Python level and
who aren't bothered by garbled user-facing output (or who are hiding stdout and
stderr from the command in question) may opt to set this to ``False`` as
needed.


.. _pseudottys:

Pseudo-terminals
================

The other main issue to consider when presenting interactive prompts to users
is that of echoing the user's own input.

Echoes
------

Typical terminal applications or bona fide text terminals (e.g. when using a
Unix system without a running GUI) present programs with a terminal device
called a tty or pty (for pseudo-terminal). These automatically echo all text
typed into them back out to the user (via stdout), as interaction without
seeing what you had just typed would be difficult. Terminal devices are also
able to conditionally turn off echoing, allowing secure password prompts.

However, it's possible for programs to be run without a tty or pty present at
all (consider cron jobs, for example) and in this situation, any stdin data
being fed to the program won't be echoed. This is desirable for programs being
run without any humans around, and it's also Fabric's old default mode of
operation.

Fabric's approach
-----------------

Unfortunately, in the context of executing commands via Fabric, when no pty is
present to echo a user's stdin, Fabric must echo it for them. This is
sufficient for many applications, but it presents problems for password
prompts, which become insecure.

In the interests of security and meeting the principle of least surprise
(insofar as users are typically expecting things to behave as they would when
run in a terminal emulator), Fabric 1.0 and greater force a pty by default.
With a pty enabled, Fabric simply allows the remote end to handle echoing or
hiding of stdin and does not echo anything itself.

.. note::
    In addition to allowing normal echo behavior, a pty also means programs
    that behave differently when attached to a terminal device will then do so.
    For example, programs that colorize output on terminals but not when run in
    the background will print colored output. Be wary of this if you inspect
    the return value of `~fabric.operations.run` or `~fabric.operations.sudo`!

For situations requiring the pty behavior turned off, the :option:`--no-pty`
command-line argument and :ref:`always-use-pty` env var may be used.


Combining the two
=================

As a final note, keep in mind that use of pseudo-terminals effectively implies
combining stdout and stderr -- in much the same way as the :ref:`combine_stderr
<combine_streams>` setting does. This is because a terminal device naturally
sends both stdout and stderr to the same place -- the user's display -- thus
making it impossible to differentiate between them.

However, at the Fabric level, the two groups of settings are distinct from one
another and may be combined in various ways. The default is for both to be set
to ``True``; the other combinations are as follows:

* ``run("cmd", pty=False, combine_stderr=True)``: will cause Fabric to echo all
  stdin itself, including passwords, as well as potentially altering ``cmd``'s
  behavior. Useful if ``cmd`` behaves undesirably when run under a pty and
  you're not concerned about password prompts.
* ``run("cmd", pty=False, combine_stderr=False)``: with both settings
  ``False``, Fabric will echo stdin and won't issue a pty -- and this is highly
  likely to result in undesired behavior for all but the simplest commands.
  However, it is also the only way to access a distinct stderr stream, which is
  occasionally useful.
* ``run("cmd", pty=True, combine_stderr=False)``: valid, but won't really make
  much of a difference, as ``pty=True`` will still result in merged streams.
  May be useful for avoiding any edge case problems in ``combine_stderr`` (none
  are presently known).
