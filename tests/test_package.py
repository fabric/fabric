"""
Tests covering the Fabric package itself (which right now is simply the version code.)
"""

from nose.tools import eq_

import fabric


def test_get_version():
    for version, version_str in [
        ((0, 2, 0, 'final'), '0.2 final'),
        ((0, 2, 1, 'final'), '0.2.1 final'),
        ((0, 2, 0, 'alpha', 0), '0.2 pre-alpha'),
        ((0, 2, 0, 'alpha', 1), '0.2 alpha 1'),
        ((0, 2, 1, 'alpha', 1), '0.2.1 alpha 1')
    ]:
        fabric.VERSION = version
        yield eq_, fabric.get_version(), version_str
