"""
Fabric's own fabfile.
"""

from __future__ import with_statement

from fabric.api import *
from fabric.contrib.project import rsync_project
# Need to import this as fabric.version for reload() purposes
import fabric.version
# But nothing is stopping us from making a convenient binding!
_version = fabric.version.get_version


def test(args=""):
    """
    Run all unit tests and doctests.

    Specify string argument ``args`` for additional args to ``nosetests``.
    """
    print(local('nosetests -sv --with-doctest %s' % args, capture=False))


def build_docs(clean='no', browse='no'):
    """
    Generate the Sphinx documentation.
    """
    c = ""
    if clean.lower() in ['yes', 'y']:
        c = "clean "
    b = ""
    if browse.lower() in ['yes', 'y']:
        b = " && open _build/html/index.html"
    local('cd docs; make %shtml%s' % (c, b), capture=False)


@hosts('jforcier@fabfile.org')
def push_docs():
    """
    Build and push the Sphinx docs to docs.fabfile.org
    """
    build_docs()
    branch = _version('branch')
    remote_loc = '/var/www/docs.fabfile/%s/' % branch
    rsync_project(remote_loc, 'docs/_build/html/', delete=True)


def _code_version_is_tagged():
    return local('git tag | egrep "^%s$"' % _version('short'))

def _update_code_version():
    """
    Update version data structure in-code and commit that change to git.
    """
    raw_input("Work has been done since last tag, version update is needed. Hit Enter to load version info in your editor: ")
    local("$EDITOR fabric/version.py", capture=False)
    # Try to detect whether user bailed out of the edit
    if not local('git diff -- fabric/version.py'):
        abort("You seem to have aborted the file edit, so I'm aborting too.")
    # Reload version module to get new version
    reload(fabric.version)
    # Commit the version update
    local("git add fabric/version.py", capture=False)
    local("git commit -m \"Cut %s\"" % _version('verbose'), capture=False)

def _commits_since_tag():
    """
    Has any work been done since the last tag?
    """
    return local("git log %s.." % _version('short'))

def tag():
    """
    Tag a new release of the software
    """
    with settings(warn_only=True):
        # Does the current in-code version exist as a Git tag already?
        # If so, this means we haven't updated the in-code version specifier
        # yet, and need to do so.
        if _code_version_is_tagged():
            # That is, if any work has been done since. Sanity check!
            if not _commits_since_tag():
                abort("No work done since last tag!")
            # Open editor, update version, commit that change to Git.
            _update_code_version()
        # If the tag doesn't exist, the user has already updated version info
        # and we can just move on.
        else:
            print("Version has already been updated, no need to edit...")
        # At this point, we've incremented the in-code version and just need to
        # tag it in Git.
        local("git tag -am \"Fabric %s\" %s" % (
            _version('verbose'),
            _version('short')
        ), capture=False)


def build():
    """
    Create distribution package via setup.py
    """
    local('python setup.py sdist', capture=False)
