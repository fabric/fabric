from __future__ import with_statement

from functools import wraps
import inspect
import sys
import textwrap

from fabric import state
from fabric.utils import abort, warn, error
from fabric.network import to_dict, normalize_to_string, disconnect_all
from fabric.context_managers import settings
from fabric.job_queue import JobQueue
from fabric.task_utils import crawl, merge, parse_kwargs
from fabric.exceptions import NetworkError

if sys.version_info[:2] == (2, 5):
    # Python 2.5 inspect.getargspec returns a tuple
    # instead of ArgSpec namedtuple.
    class ArgSpec(object):
        def __init__(self, args, varargs, keywords, defaults):
            self.args = args
            self.varargs = varargs
            self.keywords = keywords
            self.defaults = defaults
            self._tuple = (args, varargs, keywords, defaults)

        def __getitem__(self, idx):
            return self._tuple[idx]

    def patched_get_argspec(func):
        return ArgSpec(*inspect._getargspec(func))

    inspect._getargspec = inspect.getargspec
    inspect.getargspec = patched_get_argspec


def get_task_details(task):
    details = [
        textwrap.dedent(task.__doc__)
        if task.__doc__
        else 'No docstring provided']
    argspec = inspect.getargspec(task)

    default_args = [] if not argspec.defaults else argspec.defaults
    num_default_args = len(default_args)
    args_without_defaults = argspec.args[:len(argspec.args) - num_default_args]
    args_with_defaults = argspec.args[-1 * num_default_args:]

    details.append('Arguments: %s' % (
        ', '.join(
            args_without_defaults + [
                '%s=%r' % (arg, default)
                for arg, default in zip(args_with_defaults, default_args)
            ])
    ))

    return '\n'.join(details)


def _get_list(env):
    def inner(key):
        return env.get(key, [])
    return inner


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
    def __init__(self, alias=None, aliases=None, default=False, name=None,
        *args, **kwargs):
        if alias is not None:
            self.aliases = [alias, ]
        if aliases is not None:
            self.aliases = aliases
        if name is not None:
            self.name = name
        self.is_default = default

    def __details__(self):
        return get_task_details(self.run)

    def run(self):
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
        func_hosts = getattr(self, 'hosts', [])
        func_roles = getattr(self, 'roles', [])
        if func_hosts or func_roles:
            return merge(func_hosts, func_roles, arg_exclude_hosts, roledefs)
        # Finally, the env is checked (which might contain globally set lists
        # from the CLI or from module-level code). This will be the empty list
        # if these have not been set -- which is fine, this method should
        # return an empty list if no hosts have been set anywhere.
        env_vars = map(_get_list(env), "hosts roles exclude_hosts".split())
        env_vars.append(roledefs)
        return merge(*env_vars)

    def get_pool_size(self, hosts, default):
        # Default parallel pool size (calculate per-task in case variables
        # change)
        default_pool_size = default or len(hosts)
        # Allow per-task override
        # Also cast to int in case somebody gave a string
        from_task = getattr(self, 'pool_size', None)
        pool_size = int(from_task or default_pool_size)
        # But ensure it's never larger than the number of hosts
        pool_size = min((pool_size, len(hosts)))
        # Inform user of final pool size for this task
        if state.output.debug:
            print("Parallel tasks now using pool size of %d" % pool_size)
        return pool_size


class WrappedCallableTask(Task):
    """
    Wraps a given callable transparently, while marking it as a valid Task.

    Generally used via `~fabric.decorators.task` and not directly.

    .. versionadded:: 1.1

    .. seealso:: `~fabric.docs.unwrap_tasks`, `~fabric.decorators.task`
    """
    def __init__(self, callable, *args, **kwargs):
        super(WrappedCallableTask, self).__init__(*args, **kwargs)
        self.wrapped = callable
        # Don't use getattr() here -- we want to avoid touching self.name
        # entirely so the superclass' value remains default.
        if hasattr(callable, '__name__'):
            if self.name == 'undefined':
                self.__name__ = self.name = callable.__name__
            else:
                self.__name__ = self.name
        if hasattr(callable, '__doc__'):
            self.__doc__ = callable.__doc__
        if hasattr(callable, '__module__'):
            self.__module__ = callable.__module__

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        return self.wrapped(*args, **kwargs)

    def __getattr__(self, k):
        return getattr(self.wrapped, k)

    def __details__(self):
        return get_task_details(self.wrapped)


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


def _execute(task, host, my_env, args, kwargs, jobs, queue, multiprocessing):
    """
    Primary single-host work body of execute()
    """
    # Log to stdout
    if state.output.running and not hasattr(task, 'return_value'):
        print("[%s] Executing task '%s'" % (host, my_env['command']))
    # Create per-run env with connection settings
    local_env = to_dict(host)
    local_env.update(my_env)
    # Set a few more env flags for parallelism
    if queue is not None:
        local_env.update({'parallel': True, 'linewise': True})
    # Handle parallel execution
    if queue is not None: # Since queue is only set for parallel
        name = local_env['host_string']
        # Wrap in another callable that:
        # * expands the env it's given to ensure parallel, linewise, etc are
        #   all set correctly and explicitly. Such changes are naturally
        #   insulted from the parent process.
        # * nukes the connection cache to prevent shared-access problems
        # * knows how to send the tasks' return value back over a Queue
        # * captures exceptions raised by the task
        def inner(args, kwargs, queue, name, env):
            state.env.update(env)
            def submit(result):
                queue.put({'name': name, 'result': result})
            try:
                key = normalize_to_string(state.env.host_string)
                state.connections.pop(key, "")
                submit(task.run(*args, **kwargs))
            except BaseException, e: # We really do want to capture everything
                # SystemExit implies use of abort(), which prints its own
                # traceback, host info etc -- so we don't want to double up
                # on that. For everything else, though, we need to make
                # clear what host encountered the exception that will
                # print.
                if e.__class__ is not SystemExit:
                    sys.stderr.write("!!! Parallel execution exception under host %r:\n" % name)
                    submit(e)
                # Here, anything -- unexpected exceptions, or abort()
                # driven SystemExits -- will bubble up and terminate the
                # child process.
                raise

        # Stuff into Process wrapper
        kwarg_dict = {
            'args': args,
            'kwargs': kwargs,
            'queue': queue,
            'name': name,
            'env': local_env,
        }
        p = multiprocessing.Process(target=inner, kwargs=kwarg_dict)
        # Name/id is host string
        p.name = name
        # Add to queue
        jobs.append(p)
    # Handle serial execution
    else:
        with settings(**local_env):
            return task.run(*args, **kwargs)

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
    ``task`` (the function itself -- not the ``@task`` decorator wrapping your
    function!) when it is called, so ``execute(mytask, 'arg1',
    kwarg1='value')`` will (once per host) invoke ``mytask('arg1',
    kwarg1='value')``.

    :returns:
        a dictionary mapping host strings to the given task's return value for
        that host's execution run. For example, ``execute(foo, hosts=['a',
        'b'])`` might return ``{'a': None, 'b': 'bar'}`` if ``foo`` returned
        nothing on host `a` but returned ``'bar'`` on host `b`.

        In situations where a task execution fails for a given host but overall
        progress does not abort (such as when :ref:`env.skip_bad_hosts
        <skip-bad-hosts>` is True) the return value for that host will be the
        error object or message.

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
    is_callable = callable(task)
    if not (is_callable or _is_task(task)):
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
        task = WrappedCallableTask(task)
    # Filter out hosts/roles kwargs
    new_kwargs, hosts, roles, exclude_hosts = parse_kwargs(kwargs)
    # Set up host list
    my_env['all_hosts'] = task.get_hosts(hosts, roles, exclude_hosts, state.env)

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
    else:
        multiprocessing = None

    # Get pool size for this task
    pool_size = task.get_pool_size(my_env['all_hosts'], state.env.pool_size)
    # Set up job queue in case parallel is needed
    queue = multiprocessing.Queue() if parallel else None
    jobs = JobQueue(pool_size, queue)
    if state.output.debug:
        jobs._debug = True

    # Call on host list
    if my_env['all_hosts']:
        # Attempt to cycle on hosts, skipping if needed
        for host in my_env['all_hosts']:
            try:
                results[host] = _execute(
                    task, host, my_env, args, new_kwargs, jobs, queue,
                    multiprocessing
                )
            except NetworkError, e:
                results[host] = e
                # Backwards compat test re: whether to use an exception or
                # abort
                if not state.env.use_exceptions_for['network']:
                    func = warn if state.env.skip_bad_hosts else abort
                    error(e.message, func=func, exception=e.wrapped)
                else:
                    raise

            # If requested, clear out connections here and not just at the end.
            if state.env.eagerly_disconnect:
                disconnect_all()

        # If running in parallel, block until job queue is emptied
        if jobs:
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
                    if isinstance(d['results'], BaseException):
                        error(err, exception=d['results'])
                    else:
                        error(err)
                results[name] = d['results']

    # Or just run once for local-only
    else:
        with settings(**my_env):
            results['<local-only>'] = task.run(*args, **new_kwargs)
    # Return what we can from the inner task executions

    return results
