"""
Tests covering Fabric's version number pretty-print functionality.
"""

from nose.tools import eq_

import fabric.version


def test_get_version():
    get_version = fabric.version.get_version
    for tup, regular_str, verbose_str, line_str in [
        ((0, 9, 0, 'final'), '0.9', '0.9 final', '0.9'),
        ((0, 9, 1, 'final'), '0.9.1', '0.9.1 final', '0.9'),
        ((0, 9, 0, 'alpha', 1), '0.9a1', '0.9 alpha 1', '0.9'),
        ((0, 9, 1, 'beta', 1), '0.9.1b1', '0.9.1 beta 1', '0.9'),
        ((0, 9, 0, 'release candidate', 1),
            '0.9rc1', '0.9 release candidate 1', '0.9')
    ]:
        fabric.version.VERSION = tup
        yield eq_, get_version(), regular_str
        yield eq_, get_version(verbose=True), verbose_str
        yield eq_, get_version(branch_only=True), line_str
