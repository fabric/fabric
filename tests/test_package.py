"""
Tests covering the Fabric package itself.
"""

from nose.tools import eq_

import fabric


def test_get_version():
    for version, version_str in [
        ((0, 2, 0, 'final'), '0.2'),
        ((0, 2, 1, 'final'), '0.2.1'),
        ((0, 2, 0, 'alpha', 1), '0.2a1'),
        ((0, 2, 1, 'beta', 1), '0.2.1b1')
    ]:
        fabric.VERSION = version
        yield eq_, fabric.get_version(), version_str
