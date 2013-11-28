"""
Fabric's own fabfile.
"""

from __future__ import with_statement

import platform

import nose

from fabric.api import local, task

import tag
from utils import msg


@task(default=True)
def test(args=None):
    """
    Run all unit tests and doctests.

    Specify string argument ``args`` for additional args to ``nosetests``.
    """
    # Default to explicitly targeting the 'tests' folder, but only if nothing
    # is being overridden.
    default_args = "-sv --with-doctest --nologcapture"
    if platform.system() != 'Darwin':
        default_args += " --with-color"
    default_args += (" " + args) if args else ""
    nose.core.run_exit(argv=[''] + default_args.split())


@task
def upload():
    """
    Build, register and upload to PyPI
    """
    with msg("Uploading to PyPI"):
        local('python setup.py sdist register upload')


@task
def release(force='no'):
    """
    Tag, push tag to Github, & upload new version to PyPI.
    """
    tag.tag(force=force, push='yes')
    upload()
