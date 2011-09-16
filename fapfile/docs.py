from __future__ import with_statement

from fapric.api import *
from fapric.contrib.project import rsync_project
from fapric.version import get_version


docs_host = 'jforcier@fapfile.org'


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


@task
@hosts(docs_host)
def push():
    """
    Build docs and zip for upload to RTD
    """
    build(clean='yes')
    v = get_version('short')
    local("cd docs/_build/html && zip -r ../%s.zip ." % v)
