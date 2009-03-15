from nose.tools import eq_

from fabric.main import parse_arguments


def test_argument_parsing():
    for args, output in [
        # Basic 
        ('abc', ('abc', [], {}, [])),
        # Arg
        ('ab:c', ('ab', ['c'], {}, [])),
        # Kwarg
        ('a:b=c', ('a', [], {'b':'c'}, [])),
        # Arg and kwarg
        ('a:b=c,d', ('a', ['d'], {'b':'c'}, [])),
        # Multiple kwargs
        ('a:b=c,d=e', ('a', [], {'b':'c','d':'e'}, [])),
        # Host
        ('abc:host=foo', ('abc', [], {}, ['foo'])),
        # Hosts with single host
        ('abc:hosts=foo', ('abc', [], {}, ['foo'])),
        # Hosts with multiple hosts
        # Note: in a real shell, one would need to quote or escape "foo;bar".
        # But in pure-Python that would get interpreted literally, so we don't.
        ('abc:hosts=foo;bar', ('abc', [], {}, ['foo', 'bar'])),
    ]:
        yield eq_, parse_arguments([args]), [output]
