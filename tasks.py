from invocations.docs import docs, www, sites, watch_docs
from invocations.testing import (
    test, integration, coverage, watch_tests, count_errors,
)
from invocations.packaging import release
from invocations import travis

from invoke import Collection
from invoke.util import LOG_FORMAT


ns = Collection(
    docs, www, test, coverage, integration, sites, watch_docs,
    watch_tests, count_errors, release, travis,
)
ns.configure({
    'tests': {
        'package': 'fabric',
        'logformat': LOG_FORMAT,
    },
    'packaging': {
        'sign': True,
        'wheel': True,
        'check_desc': True,
    },
    # TODO: perhaps move this into a tertiary, non automatically loaded, conf
    # file so that both this & the code under test can reference it? Meh.
    'travis': {
        'sudo': {
            'user': 'sudouser',
            'password': 'mypass',
        },
    },
})
