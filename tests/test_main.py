from fudge.patcher import with_patched_object
from nose.tools import eq_, raises

from fabric.decorators import hosts, roles
from fabric.main import get_hosts, parse_arguments, _merge
import fabric.state
from fabric.state import _AttributeDict

from utils import mock_streams


def test_argument_parsing():
    for args, output in [
        # Basic 
        ('abc', ('abc', [], {}, [], [])),
        # Arg
        ('ab:c', ('ab', ['c'], {}, [], [])),
        # Kwarg
        ('a:b=c', ('a', [], {'b':'c'}, [], [])),
        # Arg and kwarg
        ('a:b=c,d', ('a', ['d'], {'b':'c'}, [], [])),
        # Multiple kwargs
        ('a:b=c,d=e', ('a', [], {'b':'c','d':'e'}, [], [])),
        # Host
        ('abc:host=foo', ('abc', [], {}, ['foo'], [])),
        # Hosts with single host
        ('abc:hosts=foo', ('abc', [], {}, ['foo'], [])),
        # Hosts with multiple hosts
        # Note: in a real shell, one would need to quote or escape "foo;bar".
        # But in pure-Python that would get interpreted literally, so we don't.
        ('abc:hosts=foo;bar', ('abc', [], {}, ['foo', 'bar'], [])),
    ]:
        yield eq_, parse_arguments([args]), [output]


def eq_hosts(command, host_list):
    eq_(set(get_hosts(command, [], [])), set(host_list))
    

def test_hosts_decorator_by_itself():
    """
    Use of @hosts only
    """
    host_list = ['a', 'b']
    @hosts(*host_list)
    def command():
        pass
    eq_hosts(command, host_list)


fake_roles = {
    'r1': ['a', 'b'],
    'r2': ['b', 'c']
}

@with_patched_object('fabric.state', 'env', _AttributeDict({'roledefs': fake_roles}))
def test_roles_decorator_by_itself():
    """
    Use of @roles only
    """
    @roles('r1')
    def command():
        pass
    eq_hosts(command, ['a', 'b'])


@with_patched_object('fabric.state', 'env', _AttributeDict({'roledefs': fake_roles}))
def test_hosts_and_roles_together():
    """
    Use of @roles and @hosts together results in union of both
    """
    @roles('r1', 'r2')
    @hosts('a')
    def command():
        pass
    eq_hosts(command, ['a', 'b', 'c'])


@with_patched_object('fabric.state', 'env', {'hosts': ['foo']})
def test_hosts_decorator_overrides_env_hosts():
    """
    If @hosts is used it replaces any env.hosts value
    """
    @hosts('bar')
    def command():
        pass
    eq_hosts(command, ['bar'])
    assert 'foo' not in get_hosts(command, [], [])


@with_patched_object('fabric.state', 'env', _AttributeDict({'roledefs': fake_roles}))
@raises(SystemExit)
@mock_streams('stderr')
def test_aborts_on_nonexistent_roles():
    """
    Aborts if any given roles aren't found
    """
    _merge([], ['badrole'])
