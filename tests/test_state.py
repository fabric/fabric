from nose.tools import eq_

from fabric.state import connections


def test_caches_same_exact_connection():
    c1 = connections['localhost']
    c2 = connections['localhost']
    eq_(c1, c2)


def test_caches_effectively_same_connection():
    c1 = connections['localhost']
    c2 = connections['jforcier@localhost']
    eq_(c1, c2)
