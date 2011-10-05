from __future__ import with_statement

from functools import wraps

from fabric import state
from fabric.utils import abort
from fabric.network import to_dict
from fabric.context_managers import settings


class Task(object):
    """
    Abstract base class for objects wishing to be picked up as Fabric tasks.

    Instances of subclasses will be treated as valid tasks when present in
    fabfiles loaded by the :doc:`fab </usage/fab>` tool.

    For details on how to implement and use `~fabric.tasks.Task` subclasses,
    please see the usage documentation on :ref:`new-style tasks
    <new-style-tasks>`.

    .. versionadded:: 1.1
    """
    name = 'undefined'
    use_task_objects = True
    aliases = None
    is_default = False

    # TODO: make it so that this wraps other decorators as expected
    def __init__(self, alias=None, aliases=None, default=False,
        *args, **kwargs):
        if alias is not None:
            self.aliases = [alias, ]
        if aliases is not None:
            self.aliases = aliases
        self.is_default = default

    def run(self):
        raise NotImplementedError


class WrappedCallableTask(Task):
    """
    Wraps a given callable transparently, while marking it as a valid Task.

    Generally used via `@task <~fabric.decorators.task>` and not directly.

    .. versionadded:: 1.1
    """
    def __init__(self, callable, *args, **kwargs):
        super(WrappedCallableTask, self).__init__(*args, **kwargs)
        self.wrapped = callable
        self.__name__ = self.name = callable.__name__
        self.__doc__ = callable.__doc__

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        return self.wrapped(*args, **kwargs)

    def __getattr__(self, k):
        return getattr(self.wrapped, k)



# For attribute tomfoolery
class _Dict(dict):
    pass

def _crawl(name, mapping):
    """
    ``name`` of ``'a.b.c'`` => ``mapping['a']['b']['c']``
    """
    key, _, rest = name.partition('.')
    value = mapping[key]
    if not rest:
        return value
    return _crawl(rest, value)

def crawl(name, mapping):
    try:
        result = _crawl(name, mapping)
        # Handle default tasks
        if isinstance(result, _Dict) and getattr(result, 'default', False):
            result = result.default
        return result
    except (KeyError, TypeError):
        return None


def _clean_hosts(host_list):
    """
    Clean host strings to ensure no trailing whitespace, etc.
    """
    return [host.strip() for host in host_list]


def _merge(hosts, roles, exclude=[]):
    """
    Merge given host and role lists into one list of deduped hosts.
    """
    # Abort if any roles don't exist
    bad_roles = [x for x in roles if x not in state.env.roledefs]
    if bad_roles:
        abort("The following specified roles do not exist:\n%s" % (
            indent(bad_roles)
        ))

    # Look up roles, turn into flat list of hosts
    role_hosts = []
    for role in roles:
        value = state.env.roledefs[role]
        # Handle "lazy" roles (callables)
        if callable(value):
            value = value()
        role_hosts += value

    # Return deduped combo of hosts and role_hosts, preserving order within
    # them (vs using set(), which may lose ordering) and skipping hosts to be
    # excluded.
    cleaned_hosts = _clean_hosts(list(hosts) + list(role_hosts))
    all_hosts = []
    for host in cleaned_hosts:
        if host not in all_hosts and host not in exclude:
            all_hosts.append(host)
    return all_hosts


def get_hosts(command, cli_hosts, cli_roles, cli_exclude_hosts):
    """
    Return the host list the given command should be using.

    See :ref:`execution-model` for detailed documentation on how host lists are
    set.
    """
    # Command line per-command takes precedence over anything else.
    if cli_hosts or cli_roles:
        return _merge(cli_hosts, cli_roles, cli_exclude_hosts)
    # Decorator-specific hosts/roles go next
    func_hosts = getattr(command, 'hosts', [])
    func_roles = getattr(command, 'roles', [])
    if func_hosts or func_roles:
        return _merge(func_hosts, func_roles, cli_exclude_hosts)
    # Finally, the env is checked (which might contain globally set lists from
    # the CLI or from module-level code). This will be the empty list if these
    # have not been set -- which is fine, this method should return an empty
    # list if no hosts have been set anywhere.
    return _merge(
        state.env['hosts'], state.env['roles'], state.env['exclude_hosts']
    )



def execute(task, *args, **kwargs):
    """
    Execute ``task`` (callable or name), honoring host/role decorators, etc.

    ``task`` may be an actual callable object, or it may be a registered task
    name, which is used to look up a callable just as if the name had been
    given on the command line (including :ref:`namespaced tasks <namespaces>`,
    e.g. ``"deploy.migrate"``.

    The task will then be executed once per host in its host list, which is
    (again) assembled in the same manner as CLI-specified tasks: drawing from
    :option:`-H`, :ref:`env.hosts <hosts>`, the `~fabric.decorators.hosts` or
    `~fabric.decorators.roles` decorators, and so forth.

    ``host``, ``hosts``, ``role``, ``roles`` and ``exclude_hosts`` kwargs will
    be stripped out of the final call, and used to set the task's host list, as
    if they had been specified on the command line like e.g. ``fab
    taskname:host=hostname``.

    Any other arguments or keyword arguments will be passed verbatim into
    ``task`` when it is called, so ``execute(mytask, 'arg1', kwarg1='value')``
    will (once per host) invoke ``mytask('arg1', kwarg1='value')``.

    .. seealso::
        :ref:`The execute usage docs <execute>`, for an expanded explanation
        and some examples.

    .. versionadded:: 1.3
    """
    my_env = {}
    # Obtain task
    if not callable(task):
        # Assume string, set env.command to it
        my_env['command'] = task
        task = crawl(task, state.commands)
        if task is None:
            abort("%r is not callable or a valid task name" % (task,))
    # Set env.command if we were given a real function or callable task obj
    else:
        dunder_name = getattr(task, '__name__', None)
        my_env['command'] = getattr(task, 'name', dunder_name)
    # Filter out hosts/roles kwargs
    new_kwargs = {}
    hosts = []
    roles = []
    exclude_hosts = []
    for key, value in kwargs.iteritems():
        if key == 'host':
            hosts = [value]
        elif key == 'hosts':
            hosts = value
        elif key == 'role':
            roles = [value]
        elif key == 'roles':
            roles = value
        elif key == 'exclude_hosts':
            exclude_hosts = value
        else:
            new_kwargs[key] = value
    # Set up host list
    my_env['all_hosts'] = get_hosts(task, hosts, roles, exclude_hosts)
    # Call on host list
    if my_env['all_hosts']:
        for host in my_env['all_hosts']:
            # Create per-run env with connection settings
            local_env = to_dict(host)
            local_env.update(my_env)
            with settings(**local_env):
                task(*args, **new_kwargs)
    # Or just run once for local-only
    else:
        with settings(**my_env):
            task(*args, **new_kwargs)
