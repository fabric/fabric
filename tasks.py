from os.path import join

from invocations import docs as _docs
from invocations.testing import test

from invoke import Collection


# TODO: move this & paramiko's copy of same into Alabaster?


d = 'sites'

# Usage doc/API site (published as docs.paramiko.org)
docs_path = join(d, 'docs')
docs_build = join(docs_path, '_build')
docs = Collection.from_module(_docs, name='docs', config={
    'sphinx': {'source': docs_path, 'target': docs_build}
})

# Main/about/changelog site ((www.)?paramiko.org)
www_path = join(d, 'www')
www = Collection.from_module(_docs, name='www', config={
    'sphinx': {'source': www_path, 'target': join(www_path, '_build')}
})


ns = Collection(docs=docs, www=www, test=test)
