"""
Internal subroutines for e.g. aborting execution with an error message,
or performing indenting on multiline output.
"""

import sys
import textwrap

def abort(msg):
    """
    Abort execution, print ``msg`` to stderr and exit with error status (1.)

    This function currently makes use of `sys.exit`_, which raises
    `SystemExit`_. Therefore, it's possible to detect and recover from inner
    calls to `abort` by using ``except SystemExit`` or similar.

    .. _sys.exit: http://docs.python.org/library/sys.html#sys.exit
    .. _SystemExit: http://docs.python.org/library/exceptions.html#exceptions.SystemExit
    """
    from fabric.state import output
    if output.aborts:
        print >> sys.stderr, "\nFatal error: " + str(msg)
        print >> sys.stderr, "\nAborting."
    sys.exit(1)


def warn(msg):
    """
    Print warning message, but do not abort execution.

    This function honors Fabric's :doc:`output controls
    <../../usage/output_controls>` and will print the given ``msg`` to stderr,
    provided that the ``warnings`` output level (which is active by default) is
    turned on.
    """
    from fabric.state import output
    if output.warnings:
        print >> sys.stderr, "\nWarning: %s\n" % msg


def indent(text, spaces=4, strip=False):
    """
    Return ``text`` indented by the given number of spaces.

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

    .. versionadded:: 0.9.2
    .. seealso:: `~fabric.utils.fastprint`
    """
    from fabric.state import output, env
    if output.user:
        prefix = ""
        if env.host_string and show_prefix:
            prefix = "[%s] " % env.host_string
        sys.stdout.write(prefix + str(text) + end)
        if flush:
            sys.stdout.flush()


def fastprint(text, show_prefix=False, end="", flush=True):
    """
    Print ``text`` immediately, without any prefix or line ending.

    This function is simply an alias of `~fabric.utils.puts` with different
    default argument values, such that the ``text`` is printed without any
    embellishment and immediately flushed.

    It is useful for any situation where you wish to print text which might
    otherwise get buffered by Python's output buffering (such as within a
    processor intensive ``for`` loop). Since such use cases typically also
    require a lack of line endings (such as printing a series of dots to
    signify progress) it also omits the traditional newline by default.

    .. note::

        Since `~fabric.utils.fastprint` calls `~fabric.utils.puts`, it is
        likewise subject to the ``user`` :doc:`output level
        </usage/output_controls>`.

    .. versionadded:: 0.9.2
    .. seealso:: `~fabric.utils.puts`
    """
    return puts(text=text, show_prefix=show_prefix, end=end, flush=flush)


def handle_prompt_abort():
    import fabric.state
    if fabric.state.env.abort_on_prompts:
        abort("Needed to prompt, but abort-on-prompts was set to True!")
