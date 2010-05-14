"""
Internal subroutines for e.g. aborting execution with an error message,
or performing indenting on multiline output.
"""

import sys
import textwrap


def abort(msg):
    """
    Abort execution, printing given message and exiting with error status.
    When not invoked as the ``fab`` command line tool, raise an exception
    instead.
    """
    from fabric.state import output
    if output.aborts:
        print >> sys.stderr, "\nFatal error: " + str(msg)
        print >> sys.stderr, "\nAborting."
    sys.exit(1)

    
def warn(msg):
    """
    Print warning message, but do not abort execution.
    """
    from fabric.state import output
    if output.warnings:
        print >> sys.stderr, "\nWarning: %s\n" % msg


def indent(text, spaces=4, strip=False):
    """
    Returns text indented by the given number of spaces.

    If text is not a string, it is assumed to be a list of lines and will be
    joined by ``\\n`` prior to indenting.

    When ``strip`` is ``True``, a minimum amount of whitespace is removed from
    the left-hand side of the given string (so that relative indents are
    preserved, but otherwise things are left-stripped). This allows you to
    effectively "normalize" any previous indentation for some inputs.
    """
    # Normalize list of strings into a string for dedenting. "list" here means
    # "not a string" meaning "doesn't have splitlines". Meh.
    if not hasattr(text, 'splitlines'):
        text = '\n'.join(text)
    # Dedent if requested
    if strip:
        text = textwrap.dedent(text)
    prefix = ' ' * spaces
    output = '\n'.join(prefix + line for line in text.splitlines())
    # Strip out empty lines before/aft
    output = output.strip()
    # Reintroduce first indent (which just got stripped out)
    output = prefix + output
    return output


def puts(text, show_prefix=True, end="\n", flush=False):
    """
    An alias for ``print`` whose output is managed by Fabric's output controls.

    In other words, this function simply prints to ``sys.stdout``, but will
    hide its output if the ``user`` :doc:`output level
    </usage/output_controls>` is set to ``False``.

    If ``show_prefix=False``, `puts` will omit the leading ``[hostname]``
    which it tacks on by default. (It will also omit this prefix if
    ``env.host_string`` is empty.)

    Newlines may be disabled by setting ``end`` to the empty string (``''``).
    (This intentionally mirrors Python 3's ``print`` syntax.)

    You may force output flushing (e.g. to bypass output buffering) by setting
    ``flush=True``.

    .. note::
        due to what appears to be a bug in the otherwise amazing Sphinx
        documentation generator, the reported default value for ``end`` in the
        above function signature is incorrect. The actual default value is a
        newline, ``"\\n"``.

    .. versionadded:: 1.0
    """
    from fabric.state import output, env
    if output.user:
        prefix = ""
        if env.host_string and show_prefix:
            prefix = "[%s] " % env.host_string
        sys.stdout.write(prefix + str(text) + end)
        if flush:
            sys.stdout.flush()
