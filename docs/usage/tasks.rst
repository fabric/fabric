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

* Decorate a regular module level function with `~fabric.decorators.task`,
  which transparently wraps the function in a `~fabric.tasks.Task` subclass.
  The function name will be used as the task name when invoking.
* Subclass `~fabric.tasks.Task` (`~fabric.tasks.Task` itself is intended to be
  abstract), define a ``run`` method, and instantiate your subclass at module
  level. Instances' ``name`` attributes are used as the task name; if omitted
  the instance's variable name will be used instead.

Use of new-style tasks also allows you to set up task namespaces -- see below.


.. _namespaces:

Namespaces
----------

With :ref:`classic tasks <classic-tasks>`, fabfiles were limited to a single,
flat set of task names with no real way to organize them.  In Fabric 1.1 and
newer, if you declare tasks the new way (via `~fabric.decorators.task` or your
own `~fabric.tasks.Task` subclass instances) you may take advantage of
**namespacing**:

* Any module objects imported into your fabfile will be recursed into, looking
  for additional task objects.
* You may further control which objects are "exported" by using the standard
  Python ``__all__`` module-level variable name (thought they should still be
  valid new-style task objects.)
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

As mentioned above, Fabric will examine any imported module objects for tasks.
For now we just want to include our own, "nearby" tasks, so we'll make a new
submodule in our package for dealing with, say, load balancers -- ``lb.py``::

    @task
    def add_backend():
        ...

And we'll add this to the top of ``__init__.py``::

    import lb

Now ``fab --list`` shows us::

    deploy
    compress
    lb.add_backend

Again, with one task, it looks kind of silly, but the benefits should be pretty
obvious.

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

It's also possible to limit what Fabric "sees" when it examines imported
modules, by using the Python convention of a module level ``__all__`` variable
(a list of variable names.) If we didn't want the ``db.migrations.run`` task to
show up by default for some reason, we could add this to the top of
``db/migrations.py``::

    __all__ = ['list']

Note the lack of ``'run'`` there. You could, if needed, import ``run`` directly
into some other part of the hierarchy, or specify ``db/migrations.py`` as the
root fabfile with ``fab -f`` (which does not consider ``__all__``.)

Switching it up
~~~~~~~~~~~~~~~

Finally, while we've been keeping our fabfile package neatly organized and
importing it in a straightforward manner, the filesystem layout doesn't
actually matter here. All Fabric's loader cares about is the names the modules
are given when they're imported.

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

.. note::

    To see exactly which callables in your fabfile may be executed via ``fab``,
    use :option:`fab --list <-l>`.

Imports
-------

Python's ``import`` statement effectively includes the imported objects in your
module's namespace. Since Fabric's fabfiles are just Python modules, this means
that imports are also considered as possible classic-style tasks, alongside
anything defined in the fabfile itself.

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
