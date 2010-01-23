from fudge.patcher import with_patched_object
from nose.tools import ok_, eq_, raises

from fabric.decorators import hosts, roles
from fabric.main import get_hosts, parse_arguments, _merge, _escape_split, load_fabfile
import fabric.state
from fabric.state import _AttributeDict

from utils import mock_streams
import os
import sys


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

@with_patched_object(
    'fabric.state', 'env', _AttributeDict({'roledefs': fake_roles})
)
def test_roles_decorator_by_itself():
    """
    Use of @roles only
    """
    @roles('r1')
    def command():
        pass
    eq_hosts(command, ['a', 'b'])


@with_patched_object(
    'fabric.state', 'env', _AttributeDict({'roledefs': fake_roles})
)
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


def test_hosts_decorator_expands_single_iterable():
    """
    @hosts(iterable) should behave like @hosts(*iterable)
    """
    host_list = ['foo', 'bar']
    @hosts(host_list)
    def command():
        pass
    eq_(command.hosts, host_list)


def test_roles_decorator_expands_single_iterable():
    """
    @roles(iterable) should behave like @roles(*iterable)
    """
    role_list = ['foo', 'bar']
    @roles(role_list)
    def command():
        pass
    eq_(command.roles, role_list)


@with_patched_object(
    'fabric.state', 'env', _AttributeDict({'roledefs': fake_roles})
)
@raises(SystemExit)
@mock_streams('stderr')
def test_aborts_on_nonexistent_roles():
    """
    Aborts if any given roles aren't found
    """
    _merge([], ['badrole'])


lazy_role = {'r1': lambda: ['a', 'b']}

@with_patched_object(
    'fabric.state', 'env', _AttributeDict({'roledefs': lazy_role})
)
def test_lazy_roles():
    """
    Roles may be callables returning lists, as well as regular lists
    """
    @roles('r1')
    def command():
        pass
    eq_hosts(command, ['a', 'b'])

def support_fabfile(name):
    return os.path.join(os.path.dirname(__file__), 'support', name)

def test_implicit_discover():
    """
    Automatically includes all functions in a fabfile
    """
    implicit = support_fabfile("implicit_fabfile.py")
    sys.path[0:0] = [os.path.dirname(implicit),]

    docs, funcs = load_fabfile(implicit)
    ok_(len(funcs) == 2)
    ok_("foo" in funcs)
    ok_("bar" in funcs)

    sys.path = sys.path[1:]

def test_explicit_discover():
    """
    Only use those methods listed in __all__
    """
    explicit = support_fabfile("explicit_fabfile.py")
    sys.path[0:0] = [os.path.dirname(explicit),]

    docs, funcs = load_fabfile(explicit)
    ok_(len(funcs) == 1)
    ok_("foo" in funcs)
    ok_("bar" not in funcs)

def test_allow_registering_modules():
    module = support_fabfile('module_fabfile.py')
    sys.path[0:0] = [os.path.dirname(module),]

    docs, funcs = load_fabfile(module)
    ok_(len(funcs) == 2)
    ok_('tasks.hello' in funcs)
    ok_('tasks.world' in funcs)

def test_modules_should_pay_attention_to_all_and_explicit_discovery():
    module = support_fabfile('module_explicit.py')
    sys.path[0:0] = [os.path.dirname(module),]

    docs, funcs = load_fabfile(module)
    ok_(len(funcs) == 1)
    ok_('tasks.hello' in funcs)
    ok_('tasks.world' not in funcs)

def test_modules_should_load_decorated_tasks_only_if_one_is_found():
    module = support_fabfile('decorated_fabfile.py')
    sys.path[0:0] = [os.path.dirname(module),]

    docs, funcs = load_fabfile(module)
    ok_(len(funcs) == 1)

