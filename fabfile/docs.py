from __future__ import with_statement

from fabric.api import *
from fabric.contrib.project import rsync_project


docs_host = 'jforcier@fabfile.org'


@task
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
    build_docs(clean='yes')
    v = _version('short')
    local("cd docs/_build/html && zip -r ../%s.zip ." % v)
