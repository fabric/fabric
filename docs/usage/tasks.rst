==============
Defining tasks
==============

As of Fabric 1.1, there are two distinct methods you may use in order to define
which objects in your fabfile show up as tasks:

* The "new" method starting in 1.1 considers instances of `~fabric.tasks.Task`
  or its subclasses, and also descends into imported modules to allow building
  nested namespaces.
* The "classic" method from 1.0 and earlier considers all public callable
  objects (functions, classes etc) and only considers the objects in the
  fabfile itself with no recursing into imported module.

.. note::
    These two methods are **mutually exclusive**: if Fabric finds *any*
    new-style task objects in your fabfile or in modules it imports, it will
    assume you've committed to this method of task declaration and won't
    consider any non-`~fabric.tasks.Task` callables. If *no* new-style tasks
    are found, it reverts to the classic behavior.

The rest of this document explores these two methods in detail.

.. note::

    To see exactly what tasks in your fabfile may be executed via ``fab``, use
    :option:`fab --list <-l>`.

.. _new-style-tasks:

New-style tasks
===============

Fabric 1.1 introduced the `~fabric.tasks.Task` class to facilitate new features
and enable some programming best practices, specifically:

* **Object-oriented tasks**. Inheritance and all that comes with it can make
  for much more sensible code reuse than passing around simple function
  objects.  The classic style of task declaration didn't entirely rule this
  out, but it also didn't make it terribly easy.
* **Namespaces**. Having an explicit method of declaring tasks makes it easier
  to set up recursive namespaces without e.g. polluting your task list with the
  contents of Python's ``os`` module (which would show up as valid "tasks"
  under the classic methodology.)

With the introduction of `~fabric.tasks.Task`, there are two ways to set up new
tasks:

* Decorate a regular module level function with `@task
  <fabric.decorators.task>`, which transparently wraps the function in a
  `~fabric.tasks.Task` subclass.  The function name will be used as the task
  name when invoking.
* Subclass `~fabric.tasks.Task` (`~fabric.tasks.Task` itself is intended to be
  abstract), define a ``run`` method, and instantiate your subclass at module
  level. Instances' ``name`` attributes are used as the task name; if omitted
  the instance's variable name will be used instead.

Use of new-style tasks also allows you to set up :ref:`namespaces
<namespaces>`.


.. _task-decorator:

The ``@task`` decorator
-----------------------

The quickest way to make use of new-style task features is to wrap basic task functions with `@task <fabric.decorators.task>`::

    from fabric.api import task, run

    @task
    def mytask():
        run("a command")


When this decorator is used, it signals to Fabric that *only* functions wrapped in the decorator are to be loaded up as valid tasks. (When not present, :ref:`classic-style task <classic-tasks>` behavior kicks in.)

.. _task-decorator-arguments:

Arguments
~~~~~~~~~

`@task <fabric.decorators.task>` may also be called with arguments to
customize its behavior. Any arguments not documented below are passed into the
constructor of the ``task_class`` being used, with the function itself as the
first argument (see :ref:`task-decorator-and-classes` for details.)

* ``task_class``: The `~fabric.tasks.Task` subclass used to wrap the decorated
  function. Defaults to `~fabric.tasks.WrappedCallableTask`.
* ``aliases``: An iterable of string names which will be used as aliases for
  the wrapped function. See :ref:`task-aliases` for details.
* ``alias``: Like ``aliases`` but taking a single string argument instead of an
  iterable. If both ``alias`` and ``aliases`` are specified, ``aliases`` will
  take precedence.
* ``default``: A boolean value determining whether the decorated task also
  stands in for its containing module as a task name. See :ref:`default-tasks`.

.. _task-aliases:

Aliases
~~~~~~~

Here's a quick example of using the ``alias`` keyword argument to facilitate
use of both a longer human-readable task name, and a shorter name which is
quicker to type::

    from fabric.api import task

    @task(alias='dwm')
    def deploy_with_migrations():
        pass

Calling :option:`--list <-l>` on this fabfile would show both the original
``deploy_with_migrations`` and its alias ``dwm``::

    $ fab --list
    Available commands:

        deploy_with_migrations
        dwm

When more than one alias for the same function is needed, simply swap in the
``aliases`` kwarg, which takes an iterable of strings instead of a single
string.

.. _default-tasks:

Default tasks
~~~~~~~~~~~~~

In a similar manner to :ref:`aliases <task-aliases>`, it's sometimes useful to
designate a given task within a module as the "default" task, which may be
called by referencing *just* the module name. This can save typing and/or
allow for neater organization when there's a single "main" task and a number
of related tasks or subroutines.

For example, a ``deploy`` submodule might contain tasks for provisioning new
servers, pushing code, migrating databases, and so forth -- but it'd be very
convenient to highlight a task as the default "just deploy" action. Such a
``deploy.py`` module might look like this::

    from fabric.api import task

    @task
    def migrate():
        pass

    @task
    def push():
        pass

    @task
    def provision():
        pass

    @task
    def full_deploy():
        if not provisioned:
            provision()
        push()
        migrate()

With the following task list (assuming a simple top level ``fabfile.py`` that just imports ``deploy``)::

    $ fab --list
    Available commands:

        deploy.full_deploy
        deploy.migrate
        deploy.provision
        deploy.push

Calling ``deploy.full_deploy`` on every deploy could get kind of old, or somebody new to the team might not be sure if that's really the right task to run.

Using the ``default`` kwarg to `@task <fabric.decorators.task>`, we can tag
e.g. ``full_deploy`` as the default task::

    @task(default=True)
    def full_deploy():
        pass

Doing so updates the task list like so::

    $ fab --list
    Available commands:

        deploy
        deploy.full_deploy
        deploy.migrate
        deploy.provision
        deploy.push

Note that ``full_deploy`` still exists as its own explicit task -- but now
``deploy`` shows up as a sort of top level alias for ``full_deploy``.

If multiple tasks within a module have ``default=True`` set, the last one to
be loaded (typically the one lowest down in the file) will take precedence.

Top-level default tasks
~~~~~~~~~~~~~~~~~~~~~~~

Using ``@task(default=True)`` in the top level fabfile will cause the denoted
task to execute when a user invokes ``fab`` without any task names (similar to
e.g. ``make``.) When using this shortcut, it is not possible to specify
arguments to the task itself -- use a regular invocation of the task if this
is necessary.

.. _task-subclasses:

``Task`` subclasses
-------------------

If you're used to :ref:`classic-style tasks <classic-tasks>`, an easy way to
think about `~fabric.tasks.Task` subclasses is that their ``run`` method is
directly equivalent to a classic task; its arguments are the task arguments
(other than ``self``) and its body is what gets executed.

For example, this new-style task::

    class MyTask(Task):
        name = "deploy"
        def run(self, environment, domain="whatever.com"):
            run("git clone foo")
            sudo("service apache2 restart")

    instance = MyTask()

is exactly equivalent to this function-based task::

    @task
    def deploy(environment, domain="whatever.com"):
        run("git clone foo")
        sudo("service apache2 restart")

Note how we had to instantiate an instance of our class; that's simply normal
Python object-oriented programming at work. While it's a small bit of
boilerplate right now -- for example, Fabric doesn't care about the name you
give the instantiation, only the instance's ``name`` attribute -- it's well
worth the benefit of having the power of classes available.

We plan to extend the API in the future to make this experience a bit smoother.

.. _task-decorator-and-classes:

Using custom subclasses with ``@task``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's possible to marry custom `~fabric.tasks.Task` subclasses with `@task
<fabric.decorators.task>`. This may be useful in cases where your core
execution logic doesn't do anything class/object-specific, but you want to
take advantage of class metaprogramming or similar techniques.

Specifically, any `~fabric.tasks.Task` subclass which is designed to take in a
callable as its first constructor argument (as the built-in
`~fabric.tasks.WrappedCallableTask` does) may be specified as the
``task_class`` argument to `@task <fabric.decorators.task>`.

Fabric will automatically instantiate a copy of the given class, passing in
the wrapped function as the first argument. All other args/kwargs given to the
decorator (besides the "special" arguments documented in
:ref:`task-decorator-arguments`) are added afterwards.

Here's a brief and somewhat contrived example to make this obvious::

    from fabric.api import task
    from fabric.tasks import Task

    class CustomTask(Task):
        def __init__(self, func, myarg):
            self.func = func
            self.myarg = myarg

        def run(self, *args, **kwargs):
            return self.func(*args, **kwargs)

    @task(task_class=CustomTask, myarg='value', alias='at')
    def actual_task():
        pass

When this fabfile is loaded, a copy of ``CustomTask`` is instantiated, effectively calling::

    task_obj = CustomTask(actual_task, myarg='value')

Note how the ``alias`` kwarg is stripped out by the decorator itself and never
reaches the class instantiation; this is identical in function to how
:ref:`command-line task arguments <task-arguments>` work.

.. _namespaces:

Namespaces
----------

With :ref:`classic tasks <classic-tasks>`, fabfiles were limited to a single,
flat set of task names with no real way to organize them.  In Fabric 1.1 and
newer, if you declare tasks the new way (via `@task <fabric.decorators.task>`
or your own `~fabric.tasks.Task` subclass instances) you may take advantage
of **namespacing**:

* Any module objects imported into your fabfile will be recursed into, looking
  for additional task objects.
* Within submodules, you may control which objects are "exported" by using the
  standard Python ``__all__`` module-level variable name (thought they should
  still be valid new-style task objects.)
* These tasks will be given new dotted-notation names based on the modules they
  came from, similar to Python's own import syntax.

Let's build up a fabfile package from simple to complex and see how this works.

Basic
~~~~~

We start with a single `__init__.py` containing a few tasks (the Fabric API
import omitted for brevity)::

    @task
    def deploy():
        ...

    @task
    def compress():
        ...

The output of ``fab --list`` would look something like this::

    deploy
    compress

There's just one namespace here: the "root" or global namespace. Looks simple
now, but in a real-world fabfile with dozens of tasks, it can get difficult to
manage.

Importing a submodule
~~~~~~~~~~~~~~~~~~~~~

As mentioned above, Fabric will examine any imported module objects for tasks,
regardless of where that module exists on your Python import path.  For now we
just want to include our own, "nearby" tasks, so we'll make a new submodule in
our package for dealing with, say, load balancers -- ``lb.py``::

    @task
    def add_backend():
        ...

And we'll add this to the top of ``__init__.py``::

    import lb

Now ``fab --list`` shows us::

    deploy
    compress
    lb.add_backend

Again, with only one task in its own submodule, it looks kind of silly, but the
benefits should be pretty obvious.

Going deeper
~~~~~~~~~~~~

Namespacing isn't limited to just one level. Let's say we had a larger setup
and wanted a namespace for database related tasks, with additional
differentiation inside that. We make a sub-package named ``db/`` and inside it,
a ``migrations.py`` module::

    @task
    def list():
        ...

    @task
    def run():
        ...

We need to make sure that this module is visible to anybody importing ``db``,
so we add it to the sub-package's ``__init__.py``::

    import migrations

As a final step, we import the sub-package into our root-level ``__init__.py``,
so now its first few lines look like this::

   import lb
   import db

After all that, our file tree looks like this::

    .
    ├── __init__.py
    ├── db
    │   ├── __init__.py
    │   └── migrations.py
    └── lb.py

and ``fab --list`` shows::

    deploy
    compress
    lb.add_backend
    db.migrations.list
    db.migrations.run

We could also have specified (or imported) tasks directly into
``db/__init__.py``, and they would show up as ``db.<whatever>`` as you might
expect.

Limiting with ``__all__``
~~~~~~~~~~~~~~~~~~~~~~~~~

You may limit what Fabric "sees" when it examines imported modules, by using
the Python convention of a module level ``__all__`` variable (a list of
variable names.) If we didn't want the ``db.migrations.run`` task to show up by
default for some reason, we could add this to the top of ``db/migrations.py``::

    __all__ = ['list']

Note the lack of ``'run'`` there. You could, if needed, import ``run`` directly
into some other part of the hierarchy, but otherwise it'll remain hidden.

Switching it up
~~~~~~~~~~~~~~~

We've been keeping our fabfile package neatly organized and importing it in a
straightforward manner, but the filesystem layout doesn't actually matter here.
All Fabric's loader cares about is the names the modules are given when they're
imported.

For example, if we changed the top of our root ``__init__.py`` to look like
this::

    import db as database

Our task list would change thusly::

    deploy
    compress
    lb.add_backend
    database.migrations.list
    database.migrations.run

This applies to any other import -- you could import third party modules into
your own task hierarchy, or grab a deeply nested module and make it appear near
the top level.

Nested list output
~~~~~~~~~~~~~~~~~~

As a final note, we've been using the default Fabric :option:`--list <-l>`
output during this section -- it makes it more obvious what the actual task
names are. However, you can get a more nested or tree-like view by passing
``nested`` to the :option:`--list-format <-F>` option::

    $ fab --list-format=nested --list
    Available commands (remember to call as module.[...].task):

        deploy
        compress
        lb:
            add_backend
        database:
            migrations:
                list
                run

While it slightly obfuscates the "real" task names, this view provides a handy
way of noting the organization of tasks in large namespaces.


.. _classic-tasks:

Classic tasks
=============

When no new-style `~fabric.tasks.Task`-based tasks are found, Fabric will
consider any callable object found in your fabfile, **except** the following:

* Callables whose name starts with an underscore (``_``). In other words,
  Python's usual "private" convention holds true here.
* Callables defined within Fabric itself. Fabric's own functions such as
  `~fabric.operations.run` and `~fabric.operations.sudo`  will not show up in
  your task list.


Imports
-------

Python's ``import`` statement effectively includes the imported objects in your
module's namespace. Since Fabric's fabfiles are just Python modules, this means
that imports are also considered as possible classic-style tasks, alongside
anything defined in the fabfile itself.

    .. note::
        This only applies to imported *callable objects* -- not modules.
        Imported modules only come into play if they contain :ref:`new-style
        tasks <new-style-tasks>`, at which point this section no longer
        applies.

Because of this, we strongly recommend that you use the ``import module`` form
of importing, followed by ``module.callable()``, which will result in a cleaner
fabfile API than doing ``from module import callable``.

For example, here's a sample fabfile which uses ``urllib.urlopen`` to get some
data out of a webservice::

    from urllib import urlopen

    from fabric.api import run

    def webservice_read():
        objects = urlopen('http://my/web/service/?foo=bar').read().split()
        print(objects)

This looks simple enough, and will run without error. However, look what
happens if we run :option:`fab --list <-l>` on this fabfile::

    $ fab --list
    Available commands:

      webservice_read   List some directories.   
      urlopen           urlopen(url [, data]) -> open file-like object

Our fabfile of only one task is showing two "tasks", which is bad enough, and
an unsuspecting user might accidentally try to call ``fab urlopen``, which
probably won't work very well. Imagine any real-world fabfile, which is likely
to be much more complex, and hopefully you can see how this could get messy
fast.

For reference, here's the recommended way to do it::

    import urllib

    from fabric.api import run

    def webservice_read():
        objects = urllib.urlopen('http://my/web/service/?foo=bar').read().split()
        print(objects)

It's a simple change, but it'll make anyone using your fabfile a bit happier.
