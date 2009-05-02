"""
Fabric's own fabfile.
"""

from fabric.api import *
from fabric.contrib import rsync_project


def test():
    """
    Run all unit tests
    """
    # Need show_stderr=True because the interesting output of nosetests is
    # actually sent to stderr, not stdout.
    print(local('nosetests -sv', show_stderr=True))


def build_docs():
    """
    Generate the Sphinx documentation
    """
    print(local('cd docs && make clean html', show_stderr=True))


@hosts('jforcier@fabfile.org')
def push_docs():
    build_docs()
    rsync_project('/var/www/docs.fabfile/', 'docs/_build/html/', delete=True)
