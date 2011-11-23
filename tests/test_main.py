from __future__ import with_statement

import copy
from operator import isMappingType
import os
import sys
from contextlib import contextmanager

from fudge import Fake, patched_context
from nose.tools import ok_, eq_, raises

from fabric.decorators import hosts, roles, task
from fabric.main import (get_hosts, parse_arguments, _merge, _escape_split,
        load_fabfile, list_commands, _task_names, _crawl, crawl,
        COMMANDS_HEADER, NESTED_REMINDER)
import fabric.state
from fabric.state import _AttributeDict
from fabric.tasks import Task

from utils import mock_streams, patched_env, eq_, FabricTest


#
# Basic CLI stuff
#

def test_argument_parsing():
    for args, output in [
        # Basic 
        ('abc', ('abc', [], {}, [], [], [])),
        # Arg
        ('ab:c', ('ab', ['c'], {}, [], [], [])),
        # Kwarg
        ('a:b=c', ('a', [], {'b':'c'}, [], [], [])),
        # Arg and kwarg
        ('a:b=c,d', ('a', ['d'], {'b':'c'}, [], [], [])),
        # Multiple kwargs
        ('a:b=c,d=e', ('a', [], {'b':'c','d':'e'}, [], [], [])),
        # Host
        ('abc:host=foo', ('abc', [], {}, ['foo'], [], [])),
        # Hosts with single host
        ('abc:hosts=foo', ('abc', [], {}, ['foo'], [], [])),
        # Hosts with multiple hosts
        # Note: in a real shell, one would need to quote or escape "foo;bar".
        # But in pure-Python that would get interpreted literally, so we don't.
        ('abc:hosts=foo;bar', ('abc', [], {}, ['foo', 'bar'], [], [])),

        # Exclude hosts
        ('abc:hosts=foo;bar,exclude_hosts=foo', ('abc', [], {}, ['foo', 'bar'], [], ['foo'])),
        ('abc:hosts=foo;bar,exclude_hosts=foo;bar', ('abc', [], {}, ['foo', 'bar'], [], ['foo','bar'])),
       # Empty string args
        ("task:x=y,z=", ('task', [], {'x': 'y', 'z': ''}, [], [], [])),
        ("task:foo,,x=y", ('task', ['foo', ''], {'x': 'y'}, [], [], [])),
    ]:
        yield eq_, parse_arguments([args]), [output]


def test_escaped_task_arg_split():
    """
    Allow backslashes to escape the task argument separator character
    """
    argstr = r"foo,bar\,biz\,baz,what comes after baz?"
    eq_(
        _escape_split(',', argstr),
        ['foo', 'bar,biz,baz', 'what comes after baz?']
    )


def test_escaped_task_kwarg_split():
    """
    Allow backslashes to escape the = in x=y task kwargs
    """
    argstr = r"cmd:arg,escaped\,arg,nota\=kwarg,regular=kwarg,escaped=regular\=kwarg"
    args = ['arg', 'escaped,arg', 'nota=kwarg']
    kwargs = {'regular': 'kwarg', 'escaped': 'regular=kwarg'}
    eq_(
        parse_arguments([argstr])[0],
        ('cmd', args, kwargs, [], [], []),
    )



#
# Host/role decorators
#

def eq_hosts(command, host_list):
    eq_(set(get_hosts(command, [], [], [])), set(host_list))

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

@patched_env({'roledefs': fake_roles})
def test_roles_decorator_by_itself():
    """
    Use of @roles only
    """
    @roles('r1')
    def command():
        pass
    eq_hosts(command, ['a', 'b'])


@patched_env({'roledefs': fake_roles})
def test_hosts_and_roles_together():
    """
    Use of @roles and @hosts together results in union of both
    """
    @roles('r1', 'r2')
    @hosts('a')
    def command():
        pass
    eq_hosts(command, ['a', 'b', 'c'])

tuple_roles = {
    'r1': ('a', 'b'),
    'r2': ('b', 'c'),
}


@patched_env({'roledefs': tuple_roles})
def test_roles_as_tuples():
    """
    Test that a list of roles as a tuple succeeds
    """
    @roles('r1')
    def command():
        pass
    eq_hosts(command, ['a', 'b'])


@patched_env({'hosts': ('foo', 'bar')})
def test_hosts_as_tuples():
    """
    Test that a list of hosts as a tuple succeeds
    """
    def command():
        pass
    eq_hosts(command, ['foo', 'bar'])


@patched_env({'hosts': ['foo']})
def test_hosts_decorator_overrides_env_hosts():
    """
    If @hosts is used it replaces any env.hosts value
    """
    @hosts('bar')
    def command():
        pass
    eq_hosts(command, ['bar'])
    assert 'foo' not in get_hosts(command, [], [], [])

@patched_env({'hosts': ['foo']})
def test_hosts_decorator_overrides_env_hosts_with_task_decorator_first():
    """
    If @hosts is used it replaces any env.hosts value even with @task
    """
    @task
    @hosts('bar')
    def command():
        pass
    eq_hosts(command, ['bar'])
    assert 'foo' not in get_hosts(command, [], [])

@patched_env({'hosts': ['foo']})
def test_hosts_decorator_overrides_env_hosts_with_task_decorator_last():
    @hosts('bar')
    @task
    def command():
        pass
    eq_hosts(command, ['bar'])
    assert 'foo' not in get_hosts(command, [], [])


@patched_env({'hosts': [' foo ', 'bar '], 'roles': [], 'exclude_hosts': []})
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

@patched_env({'roledefs': spaced_roles})
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


#
# Host exclusion
#

def dummy(): pass

def test_get_hosts_excludes_cli_exclude_hosts_from_cli_hosts():
    assert 'foo' not in get_hosts(dummy, ['foo', 'bar'], [], ['foo'])

def test_get_hosts_excludes_cli_exclude_hosts_from_decorator_hosts():
    assert 'foo' not in get_hosts(hosts('foo', 'bar')(dummy), [], [], ['foo'])

@patched_env({'hosts': ['foo', 'bar'], 'exclude_hosts': ['foo']})
def test_get_hosts_excludes_global_exclude_hosts_from_global_hosts():
    assert 'foo' not in get_hosts(dummy, [], [], [])



#
# Basic role behavior
#

@patched_env({'roledefs': fake_roles})
@raises(SystemExit)
@mock_streams('stderr')
def test_aborts_on_nonexistent_roles():
    """
    Aborts if any given roles aren't found
    """
    _merge([], ['badrole'])


lazy_role = {'r1': lambda: ['a', 'b']}

@patched_env({'roledefs': lazy_role})
def test_lazy_roles():
    """
    Roles may be callables returning lists, as well as regular lists
    """
    @roles('r1')
    def command():
        pass
    eq_hosts(command, ['a', 'b'])


#
# Fabfile loading
#

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


#
# Namespacing and new-style tasks
#

def fabfile(name):
    return os.path.join(os.path.dirname(__file__), 'support', name)

@contextmanager
def path_prefix(module):
    i = 0
    sys.path.insert(i, os.path.dirname(module))
    yield
    sys.path.pop(i)

class TestNamespaces(FabricTest):
    def setup(self):
        # Parent class preserves current env
        super(TestNamespaces, self).setup()
        # Reset new-style-tests flag so running tests via Fab itself doesn't
        # muck with it.
        import fabric.state
        if 'new_style_tasks' in fabric.state.env:
            del fabric.state.env['new_style_tasks']

    def test_implicit_discovery(self):
        """
        Default to automatically collecting all tasks in a fabfile module
        """
        implicit = fabfile("implicit_fabfile.py")
        with path_prefix(implicit):
            docs, funcs = load_fabfile(implicit)
            eq_(len(funcs), 2)
            ok_("foo" in funcs)
            ok_("bar" in funcs)

    def test_explicit_discovery(self):
        """
        If __all__ is present, only collect the tasks it specifies
        """
        explicit = fabfile("explicit_fabfile.py")
        with path_prefix(explicit):
            docs, funcs = load_fabfile(explicit)
            eq_(len(funcs), 1)
            ok_("foo" in funcs)
            ok_("bar" not in funcs)

    def test_should_load_decorated_tasks_only_if_one_is_found(self):
        """
        If any new-style tasks are found, *only* new-style tasks should load
        """
        module = fabfile('decorated_fabfile.py')
        with path_prefix(module):
            docs, funcs = load_fabfile(module)
            eq_(len(funcs), 1)
            ok_('foo' in funcs)

    def test_class_based_tasks_are_found_with_proper_name(self):
        """
        Wrapped new-style tasks should preserve their function names
        """
        module = fabfile('decorated_fabfile_with_classbased_task.py')
        from fabric.state import env
        with path_prefix(module):
            docs, funcs = load_fabfile(module)
            eq_(len(funcs), 1)
            ok_('foo' in funcs)

    def test_recursion_steps_into_nontask_modules(self):
        """
        Recursive loading will continue through modules with no tasks
        """
        module = fabfile('deep')
        with path_prefix(module):
            docs, funcs = load_fabfile(module)
            eq_(len(funcs), 1)
            ok_('submodule.subsubmodule.deeptask' in _task_names(funcs))

    def test_newstyle_task_presence_skips_classic_task_modules(self):
        """
        Classic-task-only modules shouldn't add tasks if any new-style tasks exist
        """
        module = fabfile('deep')
        with path_prefix(module):
            docs, funcs = load_fabfile(module)
            eq_(len(funcs), 1)
            ok_('submodule.classic_task' not in _task_names(funcs))


#
# --list output
#

def eq_output(docstring, format_, expected):
    return eq_(
        "\n".join(list_commands(docstring, format_)),
        expected
    )

def list_output(module, format_, expected):
    module = fabfile(module)
    with path_prefix(module):
        docstring, tasks = load_fabfile(module)
        with patched_context(fabric.state, 'commands', tasks):
            eq_output(docstring, format_, expected)

def test_list_output():
    lead = ":\n\n    "
    normal_head = COMMANDS_HEADER + lead
    nested_head = COMMANDS_HEADER + NESTED_REMINDER + lead
    for desc, module, format_, expected in (
        ("shorthand (& with namespacing)", 'deep', 'short', "submodule.subsubmodule.deeptask"),
        ("normal (& with namespacing)", 'deep', 'normal', normal_head + "submodule.subsubmodule.deeptask"),
        ("normal (with docstring)", 'docstring', 'normal', normal_head + "foo  Foos!"),
        ("nested (leaf only)", 'deep', 'nested', nested_head + """submodule:
        subsubmodule:
            deeptask"""),
        ("nested (full)", 'tree', 'nested', nested_head + """build_docs
    deploy
    db:
        migrate
    system:
        install_package
        debian:
            update_apt"""),
    ):
        list_output.description = "--list output: %s" % desc
        yield list_output, module, format_, expected
        del list_output.description


def name_to_task(name):
    t = Task()
    t.name = name
    return t

def strings_to_tasks(d):
    ret = {}
    for key, value in d.iteritems():
        if isMappingType(value):
            val = strings_to_tasks(value)
        else:
            val = name_to_task(value)
        ret[key] = val
    return ret

def test_task_names():
    for desc, input_, output in (
        ('top level (single)', {'a': 5}, ['a']),
        ('top level (multiple, sorting)', {'a': 5, 'b': 6}, ['a', 'b']),
        ('just nested', {'a': {'b': 5}}, ['a.b']),
        ('mixed', {'a': 5, 'b': {'c': 6}}, ['a', 'b.c']),
        ('top level comes before nested', {'z': 5, 'b': {'c': 6}}, ['z', 'b.c']),
        ('peers sorted equally', {'z': 5, 'b': {'c': 6}, 'd': {'e': 7}}, ['z', 'b.c', 'd.e']),
        (
            'complex tree',
            {
                'z': 5,
                'b': {
                    'c': 6,
                    'd': {
                        'e': {
                            'f': '7'
                        }
                    },
                    'g': 8
                },
                'h': 9,
                'w': {
                    'y': 10
                }
            },
            ['h', 'z', 'b.c', 'b.g', 'b.d.e.f', 'w.y']
        ),
    ):
        eq_.description = "task name flattening: %s" % desc
        yield eq_, _task_names(strings_to_tasks(input_)), output
        del eq_.description


def test_crawl():
    for desc, name, mapping, output in (
        ("base case", 'a', {'a': 5}, 5),
        ("one level", 'a.b', {'a': {'b': 5}}, 5),
        ("deep", 'a.b.c.d.e', {'a': {'b': {'c': {'d': {'e': 5}}}}}, 5),
        ("full tree", 'a.b.c', {'a': {'b': {'c': 5}, 'd': 6}, 'z': 7}, 5)
    ):
        eq_.description = "crawling dotted names: %s" % desc
        yield eq_, _crawl(name, mapping), output
        del eq_.description


def test_mapping_task_classes():
    """
    Task classes implementing the mapping interface shouldn't break --list
    """
    docstring, tasks = load_fabfile(fabfile('mapping'))
    list_output('mapping', 'normal', COMMANDS_HEADER + """:\n
    mapping_task""")
