from invocations.docs import docs, www, sites, watch_docs
from invocations.testing import (
    test, integration, coverage, watch_tests, count_errors,
)
from invocations import packaging

from invoke import Collection
from invoke.util import LOG_FORMAT


ns = Collection(
    docs, www, test, coverage, integration, sites, watch_docs,
    watch_tests, count_errors, release=packaging,
)
ns.configure({
    'tests': {
        'package': 'fabric',
        'logformat': LOG_FORMAT,
    }
})
