"""
Fabric's own fabfile.
"""

from __future__ import with_statement

import inspect

from fabric.api import *
from fabric.contrib.project import rsync_project
import fabric.version
from fabric.main import internals # For doc introspection stuff

import os.path



def test():
    """
    Run all unit tests
    """
    # Need show_stderr=True because the interesting output of nosetests is
    # actually sent to stderr, not stdout.
    print(local('nosetests -sv', capture=False))


def update_doc_signatures():
    """
    Update API autodocs with correct signatures for wrapped functions.
    """
    for name, d in internals.iteritems():
        item = d['callable']
        module_name = d['module_name']
        if hasattr(item, 'wrapped'):
            wrapped = item.wrapped
            if callable(wrapped): # Just in case...
                args = inspect.formatargspec(*inspect.getargspec(wrapped))
                name = wrapped.__name__
                funcspec = "    .. autofunction:: " + name
                argspec = funcspec + args + '\n'
                # Only update docs that actually exist
                path = 'docs/api/%s.rst' % module_name
                if os.path.exists(path):
                    # Read in lines
                    with open(path) as fd:
                        lines = fd.readlines()

                    # Update argument specification if it's outdated
                    if argspec not in lines:
                        # If previous line containing name + ( exists, nuke it
                        previous_index = None
                        for i, line in enumerate(lines):
                            if (funcspec + '(') in line:
                                del lines[i]
                                previous_index = i
                                break
                        # Regardless, append ours now that we're sure any old
                        # version is gone.
                        # Replace pre-existing line if possible
                        if previous_index is not None:
                            lines.insert(previous_index, argspec)
                        # Otherwise, just append to the end
                        else:
                            lines.append(argspec)

                    # Ensure item is excluded from being automatically found,
                    # otherwise it will show up twice.
                    # First, see if an exclude-members line exists (and also
                    # look for the :members: line, which must exist)
                    exclude_index = None
                    members_index = None
                    exclude_prefix = "    :exclude-members: "
                    for i, line in enumerate(lines):
                        if line.startswith(exclude_prefix):
                            exclude_index = i
                        if line.startswith("    :members:"):
                            members_index = i
                    # Sanity check
                    if members_index is None:
                        abort("%s lacks a members line, something's fishy!" % path)
                    # No line found: make one after the members line
                    if exclude_index is None:
                        exclude = exclude_prefix + name + '\n'
                        lines.insert(members_index + 1, exclude)
                        # Also need to make sure a blank line is between these
                        # args and the body, else Sphinx blows up.
                        lines.insert(members_index + 2, '\n')
                    # Line found: append if not already in line
                    elif name not in lines[exclude_index]:
                        line = lines[exclude_index]
                        line = line.rstrip()
                        line += u", %s\n" % name
                        lines[exclude_index] = line

                    # Now that we've tweaked the lines, write back to file.
                    with open(path, 'w') as fd:
                        fd.writelines(lines)


def build_docs():
    """
    Generate the Sphinx documentation.
    """
    print(local('cd docs && make clean html', capture=False))
    update_doc_signatures()


@hosts('jforcier@fabfile.org')
def push_docs():
    """
    Build and push the Sphinx docs to docs.fabfile.org
    """
    build_docs()
    rsync_project('/var/www/docs.fabfile/', 'docs/_build/html/', delete=True)


def tag():
    """
    Tag a new release of the software
    """
    with setenv(warn_only=True):
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
