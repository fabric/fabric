from os import getcwd
import sys

from invocations import ci
from invocations.checks import blacken
from invocations.docs import docs, www, sites, watch_docs
from invocations.pytest import (
    test,
    integration as integration_,
    coverage as coverage_,
)
from invocations.packaging import release

from invoke import Collection, task


@task
def safety_test_v1_to_v2_shim(c):
    """
    Run some very quick in-process safety checks on a dual fabric1-v-2 env.

    Assumes Fabric 2+ is already installed as 'fabric2'.
    """
    c.run("pip install 'fabric<2'")
    # Make darn sure the two copies of fabric are coming from install root, not
    # local directory - which would result in 'fabric' always being v2!
    for serious in (getcwd(), ""):
        if serious in sys.path:  # because why would .remove be idempotent?!
            sys.path.remove(serious)

    from fabric.api import env
    from fabric2 import Connection

    env.gateway = "some-gateway"
    env.no_agent = True
    env.password = "sikrit"
    env.user = "admin"
    env.host_string = "localghost"
    env.port = "2222"
    cxn = Connection.from_v1(env)
    config = cxn.config
    assert config.run.pty is True
    assert config.gateway == "some-gateway"
    assert config.connect_kwargs.password == "sikrit"
    assert config.sudo.password == "sikrit"
    assert cxn.host == "localghost"
    assert cxn.user == "admin"
    assert cxn.port == 2222


# TODO: as usual, this just wants a good pattern for "that other task, with a
# tweaked default arg value"
@task
def integration(
    c,
    opts=None,
    pty=True,
    x=False,
    k=None,
    verbose=True,
    color=True,
    capture="no",
    module=None,
):
    return integration_(c, opts, pty, x, k, verbose, color, capture, module)


# NOTE: copied from invoke's tasks.py
@task
def coverage(c, report="term", opts="", codecov=False):
    """
    Run pytest in coverage mode. See `invocations.pytest.coverage` for details.
    """
    # Use our own test() instead of theirs.
    # Also add integration test so this always hits both.
    coverage_(
        c,
        report=report,
        opts=opts,
        tester=test,
        additional_testers=[integration],
        codecov=codecov,
    )


ns = Collection(
    blacken,
    ci,
    coverage,
    docs,
    integration,
    release,
    sites,
    test,
    watch_docs,
    www,
    safety_test_v1_to_v2_shim,
)
ns.configure(
    {
        "packaging": {
            # NOTE: this is currently for identifying the source directory.
            # Should it get used for actual releasing, needs changing.
            "package": "fabric",
            "sign": True,
            "wheel": True,
            "check_desc": True,
            "changelog_file": "sites/www/changelog.rst",
            "rebuild_with_env": dict(PACKAGE_AS_FABRIC2="yes"),
        }
    }
)
