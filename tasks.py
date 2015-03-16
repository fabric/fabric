from os.path import join

from invocations import docs as _docs
from invocations.testing import test

from invoke import Collection


# TODO: move this & paramiko's copy of same into Alabaster? Invocations?


d = 'sites'

# Usage doc/API site (published as docs.fabfile.org)
docs_path = join(d, 'docs')
docs = Collection.from_module(_docs, name='docs', config={
    'sphinx': {'source': docs_path, 'target': join(docs_path, '_build')}
})
docs['build'].__doc__ = "Build the API docs subsite."

# Main/about/changelog site ((www.)?fabfile.org)
www_path = join(d, 'www')
www = Collection.from_module(_docs, name='www', config={
    'sphinx': {'source': www_path, 'target': join(www_path, '_build')}
})
www['build'].__doc__ = "Build the main project website."


ns = Collection(docs=docs, www=www, test=test)
