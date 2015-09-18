=============================
The ``fab`` command-line tool
=============================

This page documents the details of Fabric's optional command-line interface,
``fab``.


Seeking & loading tasks
=======================

``fab`` follows all the same rules as Invoke's :ref:`collection loading
<collection-discovery>`, with the sole exception that the default collection
name sought is ``fabfile`` instead of ``tasks``. Thus, whenever Invoke's
documentation mentions ``tasks`` or ``tasks.py``, Fabric substitutes
``fabfile`` / ``fabfile.py``.

For example, if your current working directory is
``/home/myuser/projects/mywebapp``, running ``fab --list`` will cause Fabric to
look for ``/home/myuser/projects/mywebapp/fabfile.py`` (or
``/home/myuser/projects/mywebapp/fabfile/__init__.py`` - Python's import system
treats both the same). If it's not found there,
``/home/myuser/projects/fabfile.py`` is sought next; and so forth.
