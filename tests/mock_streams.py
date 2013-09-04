"""
Stand-alone stream mocking decorator for easier imports.
"""
from functools import wraps
import sys
from StringIO import StringIO  # No need for cStringIO at this time


class CarbonCopy(StringIO):
    """
    A StringIO capable of multiplexing its writes to other buffer objects.
    """

    def __init__(self, buffer='', cc=None):
        """
        If ``cc`` is given and is a file-like object or an iterable of same,
        it/they will be written to whenever this StringIO instance is written
        to.
        """
        StringIO.__init__(self, buffer)
        if cc is None:
            cc = []
        elif hasattr(cc, 'write'):
            cc = [cc]
        self.cc = cc

    def write(self, s):
        StringIO.write(self, s)
        for writer in self.cc:
            writer.write(s)


def mock_streams(which):
    """
    Replaces a stream with a ``StringIO`` during the test, then restores after.

    Must specify which stream (stdout, stderr, etc) via string args, e.g.::

        @mock_streams('stdout')
        def func():
            pass

        @mock_streams('stderr')
        def func():
            pass

        @mock_streams('both')
        def func()
            pass

    If ``'both'`` is specified, not only will both streams be replaced with
    StringIOs, but a new combined-streams output (another StringIO) will appear
    at ``sys.stdall``. This StringIO will resemble what a user sees at a
    terminal, i.e. both streams intermingled.
    """
    both = (which == 'both')
    stdout = (which == 'stdout') or both
    stderr = (which == 'stderr') or both

    def mocked_streams_decorator(func):
        @wraps(func)
        def inner_wrapper(*args, **kwargs):
            if both:
                sys.stdall = StringIO()
                fake_stdout = CarbonCopy(cc=sys.stdall)
                fake_stderr = CarbonCopy(cc=sys.stdall)
            else:
                fake_stdout, fake_stderr = StringIO(), StringIO()
            if stdout:
                my_stdout, sys.stdout = sys.stdout, fake_stdout
            if stderr:
                my_stderr, sys.stderr = sys.stderr, fake_stderr
            try:
                ret = func(*args, **kwargs)
            finally:
                if stdout:
                    sys.stdout = my_stdout
                if stderr:
                    sys.stderr = my_stderr
                if both:
                    del sys.stdall
        return inner_wrapper
    return mocked_streams_decorator


