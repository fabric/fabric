"""
Functions providing integration with the Django web framework.
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

    For example, to import some models from a Django project::

        from fabric.contrib import django

        django.settings_module('myproject.settings')
        from myproject.myapp.models import MyModelClass

        def print_models():
            for instance in MyModelClass.objects.all():
                print(instance.attribute)

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
    to use this functionality. Another example (which would also work for
    `settings_module`, as they are functionally equivalent)::

        from fabric.contrib import django

        django.project('myproject')
        from django.conf import settings as django_settings

        def print_database_info():
            print("User: %s" % django_settings.DATABASE_USER)
            print("Password: %s" % django_settings.DATABASE_PASSWORD)
    """
    settings_module('%s.settings' % name)
