from __future__ import with_statement

from contextlib import nested

from fabric.api import *

# Need to import this as fabric.version for reload() purposes
import fabric.version
# But nothing is stopping us from making a convenient binding!
_version = fabric.version.get_version

from utils import msg


def is_tagged():
    with nested(hide('running'), msg("Searching for existing tag")):
        cmd = 'git tag | egrep "^%s$"' % _version('short')
        return local(cmd, capture=True)

def update_version(force):
    """
    Update version data structure in-code and commit that change to git.

    Normally, if the version file has not been modified, we abort assuming the
    user quit without saving. Specify ``force=yes`` to override this.
    """
    version_file = "fabric/version.py"
    raw_input("Version update required! Press Enter to load $EDITOR.")
    with hide('running'):
        local("$EDITOR %s" % version_file)
    # Try to detect whether user bailed out of the edit
    with hide('running'):
        has_diff = local("git diff -- %s" % version_file, capture=True)
    if not has_diff and not force:
        abort("You seem to have aborted the file edit, so I'm aborting too.")
    # Reload version module to get new version
    reload(fabric.version)
    # Commit the version update
    with msg("Committing updated version file to git"):
        local("git add %s" % version_file)
        local("git commit -m \"Cut %s\"" % _version('verbose'))

def commits_since_last_tag():
    """
    Has any work been done since the last tag?
    """
    with hide('running'):
        return local("git log %s.." % _version('short'), capture=True)


@task
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
        if is_tagged():
            # That is, if any work has been done since. Sanity check!
            if not commits_since_last_tag() and not force:
                abort("No work done since last tag!")
            # Open editor, update version, commit that change to Git.
            update_version(force)
        # If the tag doesn't exist, the user has already updated version info
        # and we can just move on.
        else:
            print("Version has already been updated, no need to edit...")
        # At this point, we've incremented the in-code version and just need to
        # tag it in Git.
        f = 'f' if force else ''
        with msg("Tagging"):
            local("git tag -%sam \"Fabric %s\" %s" % (
                f,
                _version('normal'),
                _version('short')
            ))
        # And push to the central server, if we were told to
        if push.lower() in ['y', 'yes']:
            with msg("Pushing"):
                local("git push origin %s" % _version('short'))
