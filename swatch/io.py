from __future__ import with_statement
from __future__ import absolute_import

import sys
import time
import re
import socket
from select import select

from swatch.state import env, output, win32
from swatch.utils import RingBuffer
from swatch.exceptions import CommandTimeout
import six

if win32:
    import msvcrt


def _endswith(char_list, substring):
    tail = char_list[-1 * len(substring):]
    substring = list(substring)
    return tail == substring


def _has_newline(bytelist):
    return '\r' in bytelist or '\n' in bytelist


def output_loop(*args, **kwargs):
    OutputLooper(*args, **kwargs).loop()


class OutputLooper(object):
    def __init__(self, chan, attr, stream, capture, timeout):
        self.chan = chan
        self.stream = stream
        self.capture = capture
        self.timeout = timeout
        self.read_func = getattr(chan, attr)
        self.prefix = "[%s] %s: " % (env.host_string, "out" if attr == 'recv'
                                     else "err")
        self.printing = getattr(output, 'stdout' if (attr == 'recv') else
                                'stderr')
        self.linewise = (env.linewise or env.parallel)
        self.reprompt = False
        self.read_size = 4096
        self.write_buffer = RingBuffer([], maxlen=len(self.prefix))

    def _flush(self, text):
        self.stream.write(text)
        # Actually only flush if not in linewise mode.
        # When linewise is set (e.g. in parallel mode) flushing makes
        # doubling-up of line prefixes, and other mixed output, more likely.
        if not env.linewise:
            self.stream.flush()
        self.write_buffer.extend(text)

    def loop(self):
        """
        Loop, reading from <chan>.<attr>(), writing to <stream> and buffering to <capture>.

        Will raise `~swatch.exceptions.CommandTimeout` if network timeouts
        continue to be seen past the defined ``self.timeout`` threshold.
        (Timeouts before then are considered part of normal short-timeout fast
        network reading; see swatch issue #733 for background.)
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
            self.prefix = ""

        start = time.time()
        while True:
            # Handle actual read
            try:
                bytelist = self.read_func(self.read_size)
            except socket.timeout:
                elapsed = time.time() - start
                if self.timeout is not None and elapsed > self.timeout:
                    raise CommandTimeout(timeout=self.timeout)
                continue
            # Empty byte == EOS
            if bytelist == '':
                # If linewise, ensure we flush any leftovers in the buffer.
                if self.linewise and line:
                    self._flush(self.prefix)
                    self._flush("".join(line))
                break
            # A None capture variable implies that we're in open_shell()
            if self.capture is None:
                # Just print directly -- no prefixes, no capturing, nada
                # And since we know we're using a pty in this mode, just go
                # straight to stdout.
                self._flush(bytelist)
            # Otherwise, we're in run/sudo and need to handle capturing and
            # prompts.
            else:
                # Print to user
                if self.printing:
                    printable_bytes = bytelist
                    # Small state machine to eat \n after \r
                    if printable_bytes[-1] == "\r":
                        seen_cr = True
                    if printable_bytes[0] == "\n" and seen_cr:
                        printable_bytes = printable_bytes[1:]
                        seen_cr = False

                    while _has_newline(printable_bytes) and printable_bytes != "":
                        # at most 1 split !
                        cr = re.search("(\r\n|\r|\n)", printable_bytes)
                        if cr is None:
                            break
                        end_of_line = printable_bytes[:cr.start(0)]
                        printable_bytes = printable_bytes[cr.end(0):]

                        if not initial_prefix_printed:
                            self._flush(self.prefix)

                        if _has_newline(end_of_line):
                            end_of_line = ''

                        if self.linewise:
                            self._flush("".join(line) + end_of_line + "\n")
                            line = []
                        else:
                            self._flush(end_of_line + "\n")
                        initial_prefix_printed = False

                    if self.linewise:
                        line += [printable_bytes]
                    else:
                        if not initial_prefix_printed:
                            self._flush(self.prefix)
                            initial_prefix_printed = True
                        self._flush(printable_bytes)

                # Now we have handled printing, handle interactivity
                read_lines = re.split(r"(\r|\n|\r\n)", bytelist)
                for fragment in read_lines:
                    # Store in capture buffer
                    self.capture += fragment
                    # Store in internal buffer
                    _buffer += fragment
                    # Handle prompts
                    expected, response = self._get_prompt_response()
                    if expected:
                        del self.capture[-1 * len(expected):]
                        self.chan.sendall(str(response) + '\n')
                    else:
                        prompt = _endswith(self.capture, env.sudo_prompt)
                        try_again = (
                            _endswith(self.capture, env.again_prompt + '\n') or
                            _endswith(self.capture, env.again_prompt + '\r\n'))
                        if prompt:
                            self.prompt()
                        elif try_again:
                            self.try_again()

        # Print trailing new line if the last thing we printed was our line
        # prefix.
        if self.prefix and "".join(self.write_buffer) == self.prefix:
            self._flush('\n')

    def try_again(self):
        # Remove text from capture buffer
        self.capture = self.capture[:len(env.again_prompt)]
        # Set state so we re-prompt the user at the next prompt.
        self.reprompt = True

    def _get_prompt_response(self):
        """
        Iterate through the request prompts dict and return the response and
        original request if we find a match
        """
        for tup in six.iteritems(env.prompts):
            if _endswith(self.capture, tup[0]):
                return tup
        return None, None


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
