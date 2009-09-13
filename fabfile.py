"""
Fabric's own fabfile.
"""

from __future__ import with_statement

from fabric.api import *
from fabric.contrib.project import rsync_project
import fabric.version


def test():
    """
    Run all unit tests and doctests.
    """
    print(local('nosetests -sv --with-doctest', capture=False))


def build_docs(clean='no'):
    """
    Generate the Sphinx documentation.
    """
    c = ""
    if clean.lower() in ['yes', 'y']:
        c = "clean "
    local('cd docs && make %shtml' % c, capture=False)


@hosts('jforcier@fabfile.org')
def push_docs():
    """
    Build and push the Sphinx docs to docs.fabfile.org
    """
    build_docs()
    branch = fabric.version.get_version(line_only=True)
    remote_loc = '/var/www/docs.fabfile/%s/' % branch
    rsync_project(remote_loc, 'docs/_build/html/', delete=True)


def tag():
    """
    Tag a new release of the software
    """
    with settings(warn_only=True):
        # Get current version string
        version = fabric.version.get_version()
        # Does that tag already exist?
        exists = local("git tag | grep %s" % version)
        if exists:
            # If no work has been done since, what's the point?
            if not local("git log %s.." % version):
                abort("No work done since last tag!")
            # If work *has* been done since, we need to make a new tag. To the
            # editor for version update!
            raw_input("Work has been done since last tag, version update is needed. Hit Enter to load version info in your editor: ")
            local("$EDITOR fabric/version.py", capture=False)
            # Reload version module to get new version
            reload(fabric.version)
        # If the tag doesn't exist, the user has already updated version info
        # and we can just move on.
        else:
            print("Version has already been updated, no need to edit...")
        # Get version strings
        verbose_version = fabric.version.get_version(verbose=True)
        short_version = fabric.version.get_version()
        # Commit the version update
        local("git add fabric/version.py")
        local("git commit -m \"Cut %s\"" % verbose_version)
        # And tag it
        local("git tag -m \"Fabric %s\" %s" % (
            verbose_version,
            short_version
        ))
