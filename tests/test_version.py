"""
Tests covering Fabric's version number pretty-print functionality.
"""

from __future__ import absolute_import
from nose.tools import eq_

import fabric.version


def test_get_version():
    get_version = fabric.version.get_version
    for tup, short, normal, verbose in [
        ((0, 9, 0, 'final', 0), '0.9.0', '0.9', '0.9 final'),
        ((0, 9, 1, 'final', 0), '0.9.1', '0.9.1', '0.9.1 final'),
        ((0, 9, 0, 'alpha', 1), '0.9a1', '0.9 alpha 1', '0.9 alpha 1'),
        ((0, 9, 1, 'beta', 1), '0.9.1b1', '0.9.1 beta 1', '0.9.1 beta 1'),
        ((0, 9, 0, 'release candidate', 1),
            '0.9rc1', '0.9 release candidate 1', '0.9 release candidate 1'),
        ((1, 0, 0, 'alpha', 0), '1.0a', '1.0 pre-alpha', '1.0 pre-alpha'),
    ]:
        fabric.version.VERSION = tup
        yield eq_, get_version('short'), short
        yield eq_, get_version('normal'), normal
        yield eq_, get_version('verbose'), verbose
