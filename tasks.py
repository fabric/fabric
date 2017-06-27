from invocations.docs import docs, www, sites, watch_docs
from invocations.pytest import test, integration, coverage
from invocations.packaging import release
from invocations import travis

from invoke import Collection
from invoke.util import LOG_FORMAT


ns = Collection(
    coverage,
    docs,
    integration,
    release,
    sites,
    test,
    travis,
    watch_docs,
    www,
)
ns.configure({
    'tests': {
        # TODO: have pytest tasks honor these?
        'package': 'fabric',
        'logformat': LOG_FORMAT,
    },
    'packaging': {
        'sign': True,
        'wheel': True,
        'check_desc': True,
    },
    # TODO: perhaps move this into a tertiary, non automatically loaded,
    # conf file so that both this & the code under test can reference it?
    # Meh.
    'travis': {
        'sudo': {
            'user': 'sudouser',
            'password': 'mypass',
        },
    },
})
