from __future__ import with_statement

from copy import copy
import sys

from fabric import state
from fabric.context_managers import settings
from fabric.exceptions import NetworkError
from fabric.job_queue import JobQueue
from fabric.network import to_dict
from fabric.task_utils import crawl, merge, parse_kwargs
from fabric.utils import abort, warn, error


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
    use_task_objects = True

    # TODO: make it so that this wraps other decorators as expected
    def __init__(self, alias=None, aliases=None, default=False,
                 *args, **kwargs):
        self.name = kwargs.get('name', None) or getattr(self, 'name', 'undefined')
        self.role = 'default'
        self.aliases = getattr(self, 'aliases', [])
        if getattr(self, 'alias', None):
            self.aliases += [self.alias]
        if aliases is not None:
            self.aliases += aliases
        if alias is not None:
            self.aliases.append(alias)
        self.is_default = default
        self.hosts = kwargs.get('hosts', None) or getattr(self, 'hosts', [])
        self.roles = kwargs.get('roles', None) or getattr(self, 'roles', [])

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        raise NotImplementedError

    def get_hosts(self, arg_hosts, arg_roles, arg_exclude_hosts, env=None):
        """
        Return the host list the given task should be using.

        See :ref:`host-lists` for detailed documentation on how host lists are
        set.
        """
        env = env or {'hosts': [], 'roles': [], 'exclude_hosts': []}
        roledefs = env.get('roledefs', {})
        # Command line per-task takes precedence over anything else.
        if arg_hosts or arg_roles:
            return merge(arg_hosts, arg_roles, arg_exclude_hosts, roledefs)
        # Decorator-specific hosts/roles go next
        if self.hosts or self.roles:
            return merge(self.hosts, self.roles, arg_exclude_hosts, roledefs)
        # Finally, the env is checked (which might contain globally set lists
        # from the CLI or from module-level code). This will be the empty list
        # if these have not been set -- which is fine, this method should
        # return an empty list if no hosts have been set anywhere.
        env_vars = [env.get(k, []) for k in ['hosts', 'roles', 'exclude_hosts']]
        env_vars.append(roledefs)
        return merge(*env_vars)

    def get_pool_size(self, hosts, default):
        # Default parallel pool size (calculate per-task in case variables
        # change)
        default_pool_size = default or len(hosts)
        # Allow per-task override
        pool_size = getattr(self, 'pool_size', default_pool_size)
        # But ensure it's never larger than the number of hosts
        pool_size = min((pool_size, len(hosts)))
        # Inform user of final pool size for this task
        if state.output.debug:
            print "Parallel tasks now using pool size of %d" % pool_size
        return pool_size

    def get_role(self, host, arg_hosts, env=None):
        """Return best guess for role for this task."""
        if host in arg_hosts or host in self.hosts:
            return 'default'

        env = env or {'roledefs': {}}
        roledefs = env.get('roledefs', {})

        for role, hosts in roledefs.iteritems():
            if host in hosts:
                return role
        else:
            return 'default'


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


def parallel_task_target(task, args, kwargs, env, queue):
    """
    Wrap in another callable that:
     * nukes the connection cache to prevent shared-access problems
     * knows how to send the tasks' return value back over a Queue
     * captures exceptions raised by the task
    """
    from fabric import state as _state
    from fabric.network import HostConnectionCache

    # Reset all connections from pre-fork
    _state.connections = HostConnectionCache()

    def submit(result):
        queue.put({'name': env.host_string, 'result': result})

    try:
        with settings(**env):
            submit(task.run(*args, **kwargs))
    except BaseException, e:  # We really do want to capture everything
        # SystemExit implies use of abort(), which prints its own
        # traceback, host info etc -- so we don't want to double up
        # on that. For everything else, though, we need to make
        # clear what host encountered the exception that will
        # print.
        if e.__class__ is not SystemExit:
            print >> sys.stderr, "!!! Parallel execution exception under host %r:" % env.host_string
            submit(e)
        # Here, anything -- unexpected exceptions, or abort()
        # driven SystemExits -- will bubble up and terminate the
        # child process.
        raise


def _execute(task, host, my_env, args, kwargs, jobs, queue):
    """
    Primary single-host work body of execute()
    """
    # Log to stdout
    if state.output.running and not hasattr(task, 'return_value'):
        print("[%s] Executing task '%s'" % (host, my_env['command']))
    # Create per-run env with connection settings
    local_env = copy(my_env)
    local_env.update(to_dict(host))

    with settings(**local_env):
        if jobs is None or queue is None:
            return task.run(*args, **kwargs)
        else:
            import multiprocessing

            # Stuff into Process wrapper
            kwarg_dict = {
                'task': task,
                'args': args,
                'kwargs': kwargs,
                'env': copy(state.env),
                'queue': queue,
            }
            kwarg_dict['env'].update({'parallel': True, 'linewise': True})

            job_name = '|'.join([task.role, host])
            p = multiprocessing.Process(target=parallel_task_target, kwargs=kwarg_dict, name=job_name)
            # Add to queue
            jobs.append(p)


def _is_task(task):
    return isinstance(task, Task)


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

    This function returns a dictionary mapping host strings to the given task's
    return value for that host's execution run. For example, ``execute(foo,
    hosts=['a', 'b'])`` might return ``{'a': None, 'b': 'bar'}`` if ``foo``
    returned nothing on host `a` but returned ``'bar'`` on host `b`.

    In situations where a task execution fails for a given host but overall
    progress does not abort (such as when :ref:`env.skip_bad_hosts
    <skip-bad-hosts>` is True) the return value for that host will be the error
    object or message.

    .. seealso::
        :ref:`The execute usage docs <execute>`, for an expanded explanation
        and some examples.

    .. versionadded:: 1.3
    .. versionchanged:: 1.4
        Added the return value mapping; previously this function had no defined
        return value.
    """
    my_env = {'clean_revert': True}
    results = {}
    # Obtain task
    if not (callable(task) or _is_task(task)):
        # Assume string, set env.command to it
        my_env['command'] = task
        task = crawl(task, state.commands)
        if task is None:
            abort("%r is not callable or a valid task name" % (task,))
    # Set env.command if we were given a real function or callable task obj
    else:
        dunder_name = getattr(task, '__name__', None)
        my_env['command'] = getattr(task, 'name', dunder_name)
    # Normalize to Task instance if we ended up with a regular callable
    if not _is_task(task):
        from fabric.decorators import task as task_decorator
        task = task_decorator(task)
    # Filter out hosts/roles kwargs
    new_kwargs, hosts, roles, exclude_hosts = parse_kwargs(kwargs)
    # Set up host list
    my_env['all_hosts'] = task.get_hosts(hosts, roles, exclude_hosts, state.env)

    # No hosts, just run once locally
    if not my_env['all_hosts']:
        with settings(**my_env):
            results['<local-only>'] = task.run(*args, **new_kwargs)
        return results

    parallel = requires_parallel(task)
    if parallel:
        # Import multiprocessing if needed, erroring out usefully
        # if it can't.
        try:
            import multiprocessing
        except ImportError:
            import traceback
            tb = traceback.format_exc()
            abort(tb + """
    At least one task needs to be run in parallel, but the
    multiprocessing module cannot be imported (see above
    traceback.) Please make sure the module is installed
    or that the above ImportError is fixed.""")

        # Get max pool size for this task
        pool_size = task.get_pool_size(my_env['all_hosts'], state.env.pool_size)
        # Set up job comms queue
        queue = multiprocessing.Queue()
        role_limits = state.env.get('role_limits', None)
        jobs = JobQueue(pool_size, queue, role_limits=role_limits, debug=state.output.debug)
    else:
        queue = None
        jobs = None

    # Attempt to cycle on hosts, skipping if needed
    for host in my_env['all_hosts']:
        task.role = task.get_role(host, hosts, state.env)
        try:
            results[host] = _execute(task, host, my_env, args, new_kwargs, jobs, queue)
        except NetworkError, e:
            results[host] = e
            # Backwards compat test re: whether to use an exception or
            # abort
            if not state.env.use_exceptions_for['network']:
                func = warn if state.env.skip_bad_hosts else abort
                error(e.message, func=func, exception=e.wrapped)
            else:
                raise

    if jobs:
        # If running in parallel, block until job queue is emptied
        err = "One or more hosts failed while executing task '%s'" % (
            my_env['command']
        )
        jobs.close()
        # Abort if any children did not exit cleanly (fail-fast).
        # This prevents Fabric from continuing on to any other tasks.
        # Otherwise, pull in results from the child run.
        ran_jobs = jobs.run()
        for name, d in ran_jobs.iteritems():
            if d['exit_code'] != 0:
                if isinstance(d['result'], BaseException):
                    error(err, exception=d['result'])
                else:
                    error(err)
            results[name] = d['result']

    # Return what we can from the inner task executions
    return results
