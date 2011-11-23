from __future__ import with_statement

from contextlib import nested

from fabric.api import *

# Need to import this as fabric.version for reload() purposes
import fabric.version
# But nothing is stopping us from making a convenient binding!
_version = fabric.version.get_version

from utils import msg


def _seek_version(cmd, txt):
    with nested(hide('running'), msg(txt)):
        cmd = cmd % _version('short')
        return local(cmd, capture=True)

def current_version_is_tagged():
    return _seek_version(
        'git tag | egrep "^%s$"',
        "Searching for existing tag"
    )

def current_version_is_changelogged(filename):
    return _seek_version(
        'egrep "^\* :release:`%s " filename',
        "Looking for changelog entry"
    )

def update_code(filename, force):
    """
    Update version data structure in-code and commit that change to git.

    Normally, if the version file has not been modified, we abort assuming the
    user quit without saving. Specify ``force=yes`` to override this.
    """
    raw_input("Version update in %r required! Press Enter to load $EDITOR." % filename)
    with hide('running'):
        local("$EDITOR %s" % filename)
    # Try to detect whether user bailed out of the edit
    with hide('running'):
        has_diff = local("git diff -- %s" % filename, capture=True)
    if not has_diff and not force:
        abort("You seem to have aborted the file edit, so I'm aborting too.")
    return filename

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
        changed = []
        # Does the current in-code version exist as a Git tag already?
        # If so, this means we haven't updated the in-code version specifier
        # yet, and need to do so.
        if current_version_is_tagged():
            # That is, if any work has been done since. Sanity check!
            if not commits_since_last_tag() and not force:
                abort("No work done since last tag!")
            # Open editor, update version
            version_file = "fabric/version.py"
            changed.append(update_code(version_file, force))
        # If the tag doesn't exist, the user has already updated version info
        # and we can just move on.
        else:
            print("Version has already been updated, no need to edit...")
        # Similar process but for the changelog.
        changelog = "docs/changelog.rst"
        if not current_version_is_changelogged(changelog):
           changed.append(update_code(changelog, force))
        else:
           print("Changelog already updated, no need to edit...")
        # Commit any changes
        if changed:
            with msg("Committing updated version and/or changelog"):
                reload(fabric.version)
                local("git add %s" % " ".join(changed))
                local("git commit -m \"Cut %s\"" % _version('verbose'))

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
