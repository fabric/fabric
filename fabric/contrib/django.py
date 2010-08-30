"""
.. versionadded:: 0.9.2

These functions streamline the process of initializing Django's settings module
environment variable. Once this is done, your fabfile may import from your
Django project, or Django itself, without requiring the use of ``manage.py``
plugins or having to set the environment variable yourself every time you use
your fabfile.

Currently, these functions only allow Fabric to interact with
local-to-your-fabfile Django installations. This is not as limiting as it
sounds; for example, you can use Fabric as a remote "build" tool as well as
using it locally. Imagine the following fabfile::

    from fabric.api import run, local, hosts, cd
    from fabric.contrib import django

    django.project('myproject')
    from myproject.myapp.models import MyModel

    def print_instances():
        for instance in MyModel.objects.all():
            print(instance)

    @hosts('production-server')
    def print_production_instances():
        with cd('/path/to/myproject'):
            run('fab print_instances')

With Fabric installed on both ends, you could execute
``print_production_instances`` locally, which would trigger ``print_instances``
on the production server -- which would then be interacting with your
production Django database.

As another example, if your local and remote settings are similar, you can use
it to obtain e.g. your database settings, and then use those when executing a
remote (non-Fabric) command. This would allow you some degree of freedom even
if Fabric is only installed locally::

    from fabric.api import run
    from fabric.contrib import django

    django.settings_module('myproject.settings')
    from django.conf import settings

    def dump_production_database():
        run('mysqldump -u %s -p=%s %s > /tmp/prod-db.sql' % (
            settings.DATABASE_USER,
            settings.DATABASE_PASSWORD,
            settings.DATABASE_NAME
        ))

The above snippet will work if run from a local, development environment, again
provided your local ``settings.py`` mirrors your remote one in terms of
database connection info.
"""

import os


def settings_module(module):
    """
    Set ``DJANGO_SETTINGS_MODULE`` shell environment variable to ``module``.

    Due to how Django works, imports from Django or a Django project will fail
    unless the shell environment variable ``DJANGO_SETTINGS_MODULE`` is
    correctly set (see `the Django settings docs
    <http://docs.djangoproject.com/en/dev/topics/settings/>`_.)

    This function provides a shortcut for doing so; call it near the top of
    your fabfile or Fabric-using code, after which point any Django imports
    should work correctly.

    .. note::

        This function sets a **shell** environment variable (via
        ``os.environ``) and is unrelated to Fabric's own internal "env"
        variables.
    """
    os.environ['DJANGO_SETTINGS_MODULE'] = module


def project(name):
    """
    Sets ``DJANGO_SETTINGS_MODULE`` to ``'<name>.settings'``.

    This function provides a handy shortcut for the common case where one is
    using the Django default naming convention for their settings file and
    location.

    Uses `settings_module` -- see its documentation for details on why and how
    to use this functionality.
    """
    settings_module('%s.settings' % name)
