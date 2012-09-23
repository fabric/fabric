from __future__ import with_statement

import sys
import time
import re
import socket
from select import select

from fabric.state import env, output, win32
from fabric.auth import get_password, set_password
import fabric.network
from fabric.network import ssh

if win32:
    import msvcrt


def _endswith(char_list, substring):
    tail = char_list[-1 * len(substring):]
    substring = list(substring)
    return tail == substring


def _has_newline(bytelist):
    return '\r' in bytelist or '\n' in bytelist


def _was_newline(capture, byte):
    """
    Determine if we are 'past' a newline and need to print the line prefix.
    """
    endswith_newline = _endswith(capture, '\n') or _endswith(capture, '\r')
    return endswith_newline and not _has_newline(bytelist)


def output_loop(chan, attr, stream, capture):
    ol = OutputLooper(chan, attr, stream, capture)
    ol.loop()


class OutputLooper(object):
    def __init__(self, chan, attr, stream, capture):
        self._chan = chan
        self._attr = attr
        self._stream = stream
        self._capture = capture
        self._read_func = getattr(chan, attr)
        self._prefix = "[%s] %s: " % (
            env.host_string,
            "out" if attr == 'recv' else "err"
        )
        self._printing = getattr(output, 'stdout' if (attr == 'recv') else 'stderr')
        self._linewise = (env.linewise or env.parallel)
        self._reprompt = False
        self._read_size = 4096

    def loop(self):
        """
        Loop, reading from <chan>.<attr>(), writing to <stream> and buffering to <capture>.
        """
        # Internal capture-buffer-like buffer, used solely for state keeping.
        # Unlike 'capture', nothing is ever purged from this.
        _buffer = []

        # Initialize loop variables
        initial_prefix_printed = False
        seen_cr = False
        line = []

        # Allow prefix to be turned off.
        if not env.output_prefix:
            self._prefix = ""

        while True:
            # Handle actual read
            try:
                bytelist = self._read_func(self._read_size)
            except socket.timeout:
                continue
            # Empty byte == EOS
            if bytelist == '':
                # If linewise, ensure we flush any leftovers in the buffer.
                if self._linewise and line:
                    self._flush(self._prefix)
                    self._flush("".join(line))
                break
            # A None capture variable implies that we're in open_shell()
            if self._capture is None:
                # Just print directly -- no prefixes, no capturing, nada
                # And since we know we're using a pty in this mode, just go
                # straight to stdout.
                self._flush(bytelist)
            # Otherwise, we're in run/sudo and need to handle capturing and
            # prompts.
            else:
                # Print to user
                if self._printing:
                    printable_bytes = bytelist
                    # Small state machine to eat \n after \r
                    if printable_bytes[-1] == "\r":
                        seen_cr = True
                    if printable_bytes[0] == "\n" and seen_cr:
                        printable_bytes = printable_bytes[1:]
                        seen_cr = False

                    while _has_newline(printable_bytes) and printable_bytes!="":
                        # at most 1 split !
                        cr = re.search("(\r\n|\r|\n)", printable_bytes)
                        if cr is None:
                            break
                        end_of_line = printable_bytes[:cr.start(0)]
                        printable_bytes = printable_bytes[cr.end(0):]

                        if not initial_prefix_printed:
                            self._flush(self._prefix)

                        if _has_newline(end_of_line):
                            end_of_line = ''

                        if self._linewise:
                            self._flush("".join(line)+end_of_line+"\n")
                            line = []
                        else:
                            self._flush(end_of_line+"\n")
                        initial_prefix_printed = False

                    if self._linewise:
                        line += [printable_bytes]
                    else:
                        if not initial_prefix_printed:
                            self._flush(self._prefix)
                            initial_prefix_printed = True
                        self._flush(printable_bytes)

                # Now we have handled printing, handle interactivity
                read_lines = re.split(r"(\r|\n|\r\n)", bytelist)
                for fragment in read_lines:
                    # Store in capture buffer
                    self._capture += fragment
                    # Store in internal buffer
                    _buffer += fragment
                    # Handle prompts
                    prompt = _endswith(self._capture, env.sudo_prompt)
                    try_again = (_endswith(self._capture, env.again_prompt + '\n')
                        or _endswith(self._capture, env.again_prompt + '\r\n'))
                    if prompt:
                        self.prompt()
                    elif try_again:
                        self.try_again()

    def prompt(self):
        # Obtain cached password, if any
        password = get_password()
        # Remove the prompt itself from the capture buffer. This is
        # backwards compatible with Fabric 0.9.x behavior; the user
        # will still see the prompt on their screen (no way to avoid
        # this) but at least it won't clutter up the captured text.
        del self._capture[-1 * len(env.sudo_prompt):]
        # If the password we just tried was bad, prompt the user again.
        if (not password) or self._reprompt:
            # Print the prompt and/or the "try again" notice if
            # output is being hidden. In other words, since we need
            # the user's input, they need to see why we're
            # prompting them.
            if not self._printing:
                self._flush(self._prefix)
                if self._reprompt:
                    self._flush(env.again_prompt + '\n' + self._prefix)
                self._flush(env.sudo_prompt)
            # Prompt for, and store, password. Give empty prompt so the
            # initial display "hides" just after the actually-displayed
            # prompt from the remote end.
            self._chan.input_enabled = False
            password = fabric.network.prompt_for_password(
                prompt=" ", no_colon=True, stream=self._stream
            )
            self._chan.input_enabled = True
            # Update env.password, env.passwords if necessary
            set_password(password)
            # Reset reprompt flag
            self._reprompt = False
        # Send current password down the pipe
        self._chan.sendall(password + '\n')
 
    def try_again(self):
        # Remove text from capture buffer
        self._capture = self._capture[:len(env.again_prompt)]
        # Set state so we re-prompt the user at the next prompt.
        self._reprompt = True

    def _flush(self, text):
        self._stream.write(text)
        self._stream.flush()


def input_loop(chan, using_pty):
    while not chan.exit_status_ready():
        if win32:
            have_char = msvcrt.kbhit()
        else:
            r, w, x = select([sys.stdin], [], [], 0.0)
            have_char = (r and r[0] == sys.stdin)
        if have_char and chan.input_enabled:
            # Send all local stdin to remote end's stdin
            byte = msvcrt.getch() if win32 else sys.stdin.read(1)
            chan.sendall(byte)
            # Optionally echo locally, if needed.
            if not using_pty and env.echo_stdin:
                # Not using fastprint() here -- it prints as 'user'
                # output level, don't want it to be accidentally hidden
                sys.stdout.write(byte)
                sys.stdout.flush()
        time.sleep(ssh.io_sleep)
