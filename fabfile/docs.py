from __future__ import with_statement

from fabric.api import *
from fabric.contrib.project import rsync_project
from fabric.version import get_version


@task(default=True)
def build(clean='no', browse_='no'):
    """
    Generate the Sphinx documentation.
    """
    c = ""
    if clean.lower() in ['yes', 'y']:
        c = "clean "
    b = ""
    with lcd('docs'):
        local('make %shtml%s' % (c, b))
    if browse_.lower() in ['yes', 'y']:
        browse()


@task
def browse():
    """
    Open the current dev docs in a browser tab.
    """
    local("open docs/_build/html/index.html")
