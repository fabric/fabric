from __future__ import with_statement

import threading
import sys
from select import select

from fabric.context_managers import settings, char_buffered
from fabric.network import prompt_for_password
from fabric.state import env, output, win32

if win32:
    import msvcrt


def _write(byte, which, buffer):
    """
    Print ``byte`` to appropriate system pipe, and flush.

    ``which`` should be one of (``'recv'``, ``'recv_stderr'``), causing
    ``_write`` to interact with ``sys.stdout`` or ``sys.stderr`` respectively,
    and also causing it to use an appropriate line prefix. It will also omit
    printing entirely depending on output controls.

    ``buffer`` should be the capture buffer for the stream in question; if
    ``_write`` determines that the buffer is currently empty, it will print an
    initial prefix in addition to any newline-trailing one.

    Returns ``byte``.
    """
    if not getattr(output, 'stdout' if (which == 'recv') else 'stderr'):
        return byte
    if which == 'recv':
        prefix = "out"
        pipe = sys.stdout
    else:
        prefix = "err"
        pipe = sys.stderr
    prefix = "[%s] %s: " % (env.host_string, prefix)
    # Print initial prefix if necessary
    if not buffer:
        pipe.write(prefix); pipe.flush()
    # Print byte itself
    pipe.write(byte); pipe.flush()
    # Print trailing prefix to start off next line, if necessary
    if byte in ("\n", "\r"):
        pipe.write(prefix); pipe.flush()
    return byte


def _endswith(char_list, substring):
    tail = char_list[-1*len(substring):]
    substring = list(substring)
    return tail == substring


def output_loop(chan, which, capture):
    def outputter(chan, which, capture):
        func = getattr(chan, which)
        byte = None
        password = env.password
        reprompt = False
        while True:
            # Handle actual read/write
            byte = func(1)
            if byte == '':
                break
            if capture is None:
                # Just print directly -- no prefixes, no capturing, nada
                # And since we know we're using a pty in this mode, just go
                # straight to stdout.
                sys.stdout.write(byte); sys.stdout.flush()
            else:
                capture += _write(byte, which, capture)
                # Handle password jazz
                prompt = _endswith(capture, env.sudo_prompt)
                try_again = (_endswith(capture, env.again_prompt + '\n')
                    or _endswith(capture, env.again_prompt + '\r\n'))
                if prompt:
                    # Remove the prompt itself from the capture buffer. This is
                    # backwards compatible with Fabric 0.9.x behavior; the user
                    # will still see the prompt on their screen (no way to avoid
                    # this) but at least it won't clutter up the captured text.
                    capture = capture[:len(env.sudo_prompt)]
                    if (not password) or reprompt:
                        # Save entered password in local and global password
                        # var.  Will have to re-enter when password changes per
                        # host, but this way a given password will persist for
                        # as long as it's valid.  Give empty prompt so the
                        # initial display "hides" just after the
                        # actually-displayed prompt from the remote end.
                        env.password = password = prompt_for_password(
                            previous=password,
                            prompt="",
                            no_colon=True
                        )
                        # Reset reprompt flag
                        reprompt = False
                    # Send current password down the pipe
                    chan.sendall(password + '\n')
                elif try_again:
                    # Remove text from capture buffer
                    capture = capture[:len(env.again_prompt)]
                    # Set state so we re-prompt the user at the next prompt.
                    reprompt = True

    thread = threading.Thread(None, outputter, which, (chan, which, capture))
    thread.setDaemon(True)
    thread.start()
    return thread


def input_loop(chan, using_pty):
    def inputter(chan, using_pty):
        with char_buffered(sys.stdin):
            while not chan.exit_status_ready():
                if win32:
                    have_char = msvcrt.kbhit()
                else:
                    r, w, x = select([sys.stdin], [], [], 0.0)
                    have_char = (r and r[0] == sys.stdin)
                if have_char:
                    # Send all local stdin to remote end's stdin
                    byte = msvcrt.getch() if win32 else sys.stdin.read(1)
                    chan.sendall(byte)
                    # Optionally echo locally, if needed.
                    if not using_pty and env.echo_stdin:
                        # Not using fastprint() here -- it prints as 'user'
                        # output level, don't want it to be accidentally hidden
                        sys.stdout.write(byte)
                        sys.stdout.flush()
    thread = threading.Thread(None, inputter, "input", (chan, using_pty))
    thread.setDaemon(True)
    thread.start()
    return thread


