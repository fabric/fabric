import sys
import copy

from fudge.patcher import with_patched_object
from fudge import Fake
from nose.tools import eq_, raises

from fabric.decorators import hosts, roles
from fabric.main import (get_hosts, parse_arguments, _merge, _escape_split,
        load_fabfile)
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
        # Empty string args
        ("task:x=y,z=", ('task', [], {'x': 'y', 'z': ''}, [], [])),
        ("task:foo,,x=y", ('task', ['foo', ''], {'x': 'y'}, [], [])),
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


@with_patched_object(
    'fabric.state', 'env', {'hosts': [' foo ', 'bar '], 'roles': []}
)
def test_hosts_stripped_env_hosts():
    """
    Make sure hosts defined in env.hosts are cleaned of extra spaces
    """
    def command():
        pass
    eq_hosts(command, ['foo', 'bar'])


spaced_roles = {
    'r1': [' a ', ' b '],
    'r2': ['b', 'c'],
}

@with_patched_object(
    'fabric.state', 'env', _AttributeDict({'roledefs': spaced_roles})
)
def test_roles_stripped_env_hosts():
    """
    Make sure hosts defined in env.roles are cleaned of extra spaces
    """
    @roles('r1')
    def command():
        pass
    eq_hosts(command, ['a', 'b'])


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


def test_escaped_task_arg_split():
    """
    Allow backslashes to escape the task argument separator character
    """
    argstr = r"foo,bar\,biz\,baz,what comes after baz?"
    eq_(
        _escape_split(',', argstr),
        ['foo', 'bar,biz,baz', 'what comes after baz?']
    )


def run_load_fabfile(path, sys_path):
    # Module-esque object
    fake_module = Fake().has_attr(__dict__={})
    # Fake __import__
    importer = Fake(callable=True).returns(fake_module)
    # Snapshot sys.path for restore
    orig_path = copy.copy(sys.path)
    # Update with fake path
    sys.path = sys_path
    # Test for side effects
    load_fabfile(path, importer=importer)
    eq_(sys.path, sys_path)
    # Restore
    sys.path = orig_path


def test_load_fabfile_should_not_remove_real_path_elements():
    for fabfile_path, sys_dot_path in (
        # Directory not in path
        ('subdir/fabfile.py', ['not_subdir']),
        ('fabfile.py', ['nope']),
        # Directory in path, but not at front
        ('subdir/fabfile.py', ['not_subdir', 'subdir']),
        ('fabfile.py', ['not_subdir', '']),
        ('fabfile.py', ['not_subdir', '', 'also_not_subdir']),
        # Directory in path, and at front already
        ('subdir/fabfile.py', ['subdir']),
        ('subdir/fabfile.py', ['subdir', 'not_subdir']),
        ('fabfile.py', ['', 'some_dir', 'some_other_dir']),
    ):
            yield run_load_fabfile, fabfile_path, sys_dot_path
