from __future__ import with_statement

from contextlib import contextmanager

from fabric.api import hide, puts


@contextmanager
def msg(txt):
    puts(txt + "...", end='', flush=True)
    with hide('everything'):
        yield
    puts("done.", show_prefix=False, flush=True)
