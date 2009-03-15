from nose.tools import eq_, with_setup

from fabric.main import parse_arguments


def test_argument_parsing():
    matches = [
        ('abc', ('abc', [], {}, [])),
        ('ab:c', ('ab', ['c'], {}, [])),
        ('a:b=c', ('a', [], {'b':'c'}, [])),
        ('a:b=c,d', ('a', ['d'], {'b':'c'}, [])),
        ('a:b=c,d=e', ('a', [], {'b':'c','d':'e'}, [])),
        ('abc:host=foo', ('abc', [], {}, ['foo'])),
        ('abc:hosts=foo', ('abc', [], {}, ['foo'])),
        # Note: in a real shell, one would need to quote or escape "foo;bar".
        # But in pure-Python that would get interpreted literally, so we don't.
        ('abc:hosts=foo;bar', ('abc', [], {}, ['foo', 'bar'])),
    ]
    for args, output in matches:
        yield eq_, parse_arguments([args]), [output]
