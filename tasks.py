from functools import partial
from os import environ

from invocations import travis
from invocations.checks import blacken
from invocations.docs import docs, www, sites, watch_docs
from invocations.pytest import test, integration as integration_, coverage
from invocations.packaging import release
from invocations.util import tmpdir

from invoke import Collection, task
from invoke.util import LOG_FORMAT


# Neuter the normal release.publish task to prevent accidents, then reinstate
# it as a custom task that does dual fabric-xxx and fabric2-xxx releases.
# TODO: tweak this once release.all_ actually works right...sigh
# TODO: if possible, try phrasing as a custom build that builds x2, and then
# convince the vanilla publish() to use that custom build instead of its local
# build?
# NOTE: this skips the dual_wheels, alt_python bits the upstream task has,
# which are at the moment purely for Invoke's sake (as it must publish explicit
# py2 vs py3 wheels due to some vendored dependencies)
@task
def publish(
    c,
    sdist=True,
    wheel=False,
    index=None,
    sign=False,
    dry_run=False,
    directory=None,
    check_desc=False,
):
    # TODO: better pattern for merging kwargs + config
    config = c.config.get("packaging", {})
    index = config.get("index", index)
    sign = config.get("sign", sign)
    check_desc = config.get("check_desc", check_desc)
    # Initial sanity check, if needed. Will die usefully.
    # TODO: this could also get factored out harder in invocations. shrug. it's
    # like 3 lines total...
    if check_desc:
        c.run("python setup.py check -r -s")
    with tmpdir(skip_cleanup=dry_run, explicit=directory) as directory:
        # Doesn't reeeeally need to be a partial, but if we start having to add
        # a kwarg to one call or the other, it's nice
        builder = partial(
            release.build, c, sdist=sdist, wheel=wheel, directory=directory
        )
        # Vanilla build
        builder()
        # Fabric 2 build
        environ["PACKAGE_AS_FABRIC2"] = "yes"
        builder()
        # Upload
        release.upload(c, directory, index, sign, dry_run)


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


# Better than nothing, since we haven't solved "pretend I have some other
# task's signature" yet...
publish.__doc__ = release.publish.__doc__
my_release = Collection(
    "release", release.build, release.status, publish, release.prepare
)

ns = Collection(
    blacken,
    coverage,
    docs,
    integration,
    my_release,
    sites,
    test,
    travis,
    watch_docs,
    www,
)
ns.configure(
    {
        "tests": {
            # TODO: have pytest tasks honor these?
            "package": "fabric",
            "logformat": LOG_FORMAT,
        },
        "packaging": {
            # NOTE: this is currently for identifying the source directory.
            # Should it get used for actual releasing, needs changing.
            "package": "fabric",
            "sign": True,
            "wheel": True,
            "check_desc": True,
            "changelog_file": "sites/www/changelog.rst",
        },
        # TODO: perhaps move this into a tertiary, non automatically loaded,
        # conf file so that both this & the code under test can reference it?
        # Meh.
        "travis": {
            "sudo": {"user": "sudouser", "password": "mypass"},
            "black": {"version": "18.6b4"},
        },
    }
)
