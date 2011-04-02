"""
Fabric's own fabfile.
"""

from __future__ import with_statement

import nose

from fabric.api import *
from fabric.contrib.project import rsync_project
# Need to import this as fabric.version for reload() purposes
import fabric.version
# But nothing is stopping us from making a convenient binding!
_version = fabric.version.get_version


docs_host = 'jforcier@fabfile.org'


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
    local('cd docs; make %shtml%s' % (c, b))


@hosts(docs_host)
def push_docs():
    """
    Build docs and zip for upload to RTD
    """
    build_docs(clean='yes')
    v = _version('short')
    local("cd docs/_build/html && zip -r ../%s.zip ." % v)


def _code_version_is_tagged():
    return local('git tag | egrep "^%s$"' % _version('short'))

def _update_code_version(force):
    """
    Update version data structure in-code and commit that change to git.

    Normally, if the version file has not been modified, we abort assuming the
    user quit without saving. Specify ``force=yes`` to override this.
    """
    version_file = "fabric/version.py"
    raw_input("Work has been done since last tag, version update is needed. Hit Enter to load version info in your editor: ")
    local("$EDITOR %s" % version_file)
    # Try to detect whether user bailed out of the edit
    if not local("git diff -- %s" % version_file) and not force:
        abort("You seem to have aborted the file edit, so I'm aborting too.")
    # Reload version module to get new version
    reload(fabric.version)
    # Commit the version update
    local("git add %s" % version_file)
    local("git commit -m \"Cut %s\"" % _version('verbose'))

def _commits_since_tag():
    """
    Has any work been done since the last tag?
    """
    return local("git log %s.." % _version('short'))

def tag(force='no', push='no'):
    """
    Tag a new release.

    Normally, if a Git tag exists matching the current version, and no Git
    commits appear after that tag, we abort assuming the user is making a
    mistake or forgot to commit their work.

    To override this -- i.e. to re-tag and re-upload -- specify ``force=yes``.
    We assume you know what you're doing if you use this.

    By default we do not push the tag remotely; specify ``push=yes`` to force a
    ``git push origin <tag>``.
    """
    force = force.lower() in ['y', 'yes']
    with settings(warn_only=True):
        # Does the current in-code version exist as a Git tag already?
        # If so, this means we haven't updated the in-code version specifier
        # yet, and need to do so.
        if _code_version_is_tagged():
            # That is, if any work has been done since. Sanity check!
            if not _commits_since_tag() and not force:
                abort("No work done since last tag!")
            # Open editor, update version, commit that change to Git.
            _update_code_version(force)
        # If the tag doesn't exist, the user has already updated version info
        # and we can just move on.
        else:
            print("Version has already been updated, no need to edit...")
        # At this point, we've incremented the in-code version and just need to
        # tag it in Git.
        f = 'f' if force else ''
        local("git tag -%sam \"Fabric %s\" %s" % (
            f,
            _version('verbose'),
            _version('short')
        ))
        # And push to the central server, if we were told to
        if push.lower() in ['y', 'yes']:
            local("git push origin %s" % _version('short'))


def build():
    """
    Build (but don't upload) via setup.py
    """
    local('python setup.py sdist')


def upload():
    """
    Build, register and upload to PyPI
    """
    local('python setup.py sdist register upload')


def release(force='no'):
    """
    Tag/push, build, upload new version and build/upload documentation.
    """
    tag(force=force, push='yes')
    upload()
