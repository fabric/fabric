from __future__ import with_statement

from functools import wraps

from fabric import state
from fabric.utils import abort
from fabric.network import to_dict, normalize_to_string
from fabric.context_managers import settings
from fabric.job_queue import JobQueue


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
    cleaned_hosts = [x.strip() for x in list(hosts) + list(role_hosts)]
    all_hosts = []
    for host in cleaned_hosts:
        if host not in all_hosts and host not in exclude:
            all_hosts.append(host)
    return all_hosts


def get_hosts(command, arg_hosts, arg_roles, arg_exclude_hosts):
    """
    Return the host list the given command should be using.

    See :ref:`execution-model` for detailed documentation on how host lists are
    set.
    """
    # Command line per-command takes precedence over anything else.
    if arg_hosts or arg_roles:
        return _merge(arg_hosts, arg_roles, arg_exclude_hosts)
    # Decorator-specific hosts/roles go next
    func_hosts = getattr(command, 'hosts', [])
    func_roles = getattr(command, 'roles', [])
    if func_hosts or func_roles:
        return _merge(func_hosts, func_roles, arg_exclude_hosts)
    # Finally, the env is checked (which might contain globally set lists from
    # the CLI or from module-level code). This will be the empty list if these
    # have not been set -- which is fine, this method should return an empty
    # list if no hosts have been set anywhere.
    return _merge(
        state.env['hosts'], state.env['roles'], state.env['exclude_hosts']
    )


def _run_task(task, args, kwargs):
    # First, try class-based tasks
    if hasattr(task, 'run') and callable(task.run):
        return task.run(*args, **kwargs)
    # Fallback to callable behavior
    return task(*args, **kwargs)


def _get_pool_size(task, hosts):
    # Default parallel pool size (calculate per-task in case variables
    # change)
    default_pool_size = state.env.pool_size or len(hosts)
    # Allow per-task override
    pool_size = getattr(task, 'pool_size', default_pool_size)
    # But ensure it's never larger than the number of hosts
    pool_size = min((pool_size, len(hosts)))
    # Inform user of final pool size for this task
    if state.output.debug:
        msg = "Parallel tasks now using pool size of %d"
        print msg % pool_size
    return pool_size


def requires_parallel(task):
    """
    Returns True if given ``task`` should be run in parallel mode.

    Specifically:

    * It's been explicitly marked with ``@parallel``, or:
    * It's *not* been explicitly marked with ``@serial`` *and* the global
      parallel option (``env.parallel``) is set to ``True``.
    """
    return (
        (state.env.parallel and not getattr(task, 'serial', False))
        or getattr(task, 'parallel', False)
    )


def _parallel_tasks(commands_to_run):
    return any(map(
        lambda x: requires_parallel(crawl(x[0], state.commands)),
        commands_to_run
    ))




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

    # Get pool size for this task
    pool_size = _get_pool_size(task, my_env['all_hosts'])
    # Set up job queue in case parallel is needed
    jobs = JobQueue(pool_size)
    if state.output.debug:
        jobs._debug = True

    # Call on host list
    if my_env['all_hosts']:
        for host in my_env['all_hosts']:
            # Log to stdout
            if state.output.running and not hasattr(task, 'return_value'):
                print("[%s] Executing task '%s'" % (host, my_env['command']))
            # Create per-run env with connection settings
            local_env = to_dict(host)
            local_env.update(my_env)
            with settings(**local_env):
                # Handle parallel execution
                if requires_parallel(task):
                    # Import multiprocessing if needed, erroring out usefully
                    # if it can't.
                    try:
                        import multiprocessing
                    except ImportError, e:
                        msg = "At least one task needs to be run in parallel, but the\nmultiprocessing module cannot be imported:"
                        msg += "\n\n\t%s\n\n" % e
                        msg += "Please make sure the module is installed or that the above ImportError is\nfixed."
                        abort(msg)

                    # Wrap in another callable that nukes the child's cached
                    # connection object, if needed, to prevent shared-socket
                    # problems.
                    def inner(*args, **kwargs):
                        key = normalize_to_string(state.env.host_string)
                        state.connections.pop(key, "")
                        _run_task(task, args, kwargs)
                    # Stuff into Process wrapper
                    p = multiprocessing.Process(target=inner, args=args,
                        kwargs=new_kwargs)
                    # Name/id is host string
                    p.name = local_env['host_string']
                    # Add to queue
                    jobs.append(p)
                # Handle serial execution
                else:
                    _run_task(task, args, new_kwargs)

        # If running in parallel, block until job queue is emptied
        if jobs:
            jobs.close()
            jobs.start()
    # Or just run once for local-only
    else:
        with settings(**my_env):
            _run_task(task, args, new_kwargs)
