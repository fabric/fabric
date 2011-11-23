"""
Fabric's own fabfile.
"""

from __future__ import with_statement

import nose

from fabric.api import *

import docs, tag
from utils import msg


@task
def test(args=None):
    """
    Run all unit tests and doctests.

    Specify string argument ``args`` for additional args to ``nosetests``.
    """
    default_args = "-sv --with-doctest --nologcapture --with-color"
    default_args += (" " + args) if args else ""
    try:
        nose.core.run(argv=[''] + default_args.split())
    except SystemExit:
        abort("Nose encountered an error; you may be missing newly added test dependencies. Try running 'pip install -r requirements.txt'.")


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
    Tag/push, build, upload new version and build/upload documentation.
    """
    tag.tag(force=force, push='yes')
    upload()
