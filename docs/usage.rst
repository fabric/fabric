=================
How to use Fabric
=================

Importing Fabric itself
=======================

Simplest method, which is not PEP8-compliant (meaning it's not best practices)::

    from fabric.api import *

Slightly better, albeit verbose, method which *is* PEP8-compliant::

    from fabric.api import run, sudo, prompt, abort, ...

.. note::
    You can also import directly from the individual submodules, e.g.
    ``from fabric.utils import abort``. However, all of Fabric's public API is
    guaranteed to be available via `fabric.api` for convenience purposes.

Importing other modules
=======================

Because of the way the ``fab`` tool runs, any callables found in your fabfile
(excepting Fabric's own callables, which it filters out) will be candidates for
execution, and will be displayed in ``fab --list``, and so forth.

This can lead to minor annoyances if you do a lot of ``from module import
callable``-style imports in your fabfile. Thus, we strongly recommend that you use ``import module`` followed by ``module.callable()`` in order to give your fabfile a clean API.

Rationale
---------

Take the following example where we need to use ``urllib.urlopen`` to get some
data out of a webservice::

    from urllib import urlopen

    from fabric.api import run

    def my_task():
        """
        List some directories.
        """
        directories = urlopen('http://my/web/service/?foo=bar').read().split()
        for directory in directories:
            run('ls %s' % directory)

This looks simple enough, and will run without error. However, look what
happens if we run ``fab --list`` on this fabfile::

    $ fab --list
    Available commands:

      my_task    List some directories.   
      urlopen    urlopen(url [, data]) -> open file-like object

Our fabfile of only one task is showing two "tasks", which is bad enough, and
an unsuspecting user might accidentally try to call ``fab urlopen``, which
probably won't work too well. Imagine any real-world fabfile, which is likely
to be much more complex, and hopefully you can see how this could get messy
fast.
