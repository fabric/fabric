from invocations.docs import docs, www
from invocations.packaging import release

from invoke import Collection


ns = Collection(docs, www, release)
ns.configure({
    'packaging': {
        'sign': True,
        'wheel': True,
        'changelog_file': 'sites/www/changelog.rst',
        'package': 'fabric',
        'version_module': 'version',
    },
})
