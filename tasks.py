import sys
import time

from invocations.docs import docs, www
from invocations.testing import test, coverage
from invocations import packaging

from invoke import Collection, Context, ctask


@ctask
def watch(c):
    """
    Watch both doc trees & rebuild them if files change.

    This includes e.g. rebuilding the API docs if the source code changes;
    rebuilding the WWW docs if the README changes; etc.
    """
    try:
        from watchdog.observers import Observer
        from watchdog.events import RegexMatchingEventHandler
    except ImportError:
        sys.exit("If you want to use this, 'pip install watchdog' first.")

    class APIBuildHandler(RegexMatchingEventHandler):
        def on_any_event(self, event):
            my_c = Context(config=c.config.clone())
            my_c.update(**docs.configuration())
            docs['build'](my_c)

    class WWWBuildHandler(RegexMatchingEventHandler):
        def on_any_event(self, event):
            my_c = Context(config=c.config.clone())
            my_c.update(**www.configuration())
            www['build'](my_c)

    # Readme & WWW triggers WWW
    www_handler = WWWBuildHandler(
        regexes=['\./README.rst', '\./sites/www'],
        ignore_regexes=['.*/\..*\.swp', '\./sites/www/_build'],
    )
    # Code and docs trigger API
    api_handler = APIBuildHandler(
        regexes=['\./invoke/', '\./sites/docs'],
        ignore_regexes=['.*/\..*\.swp', '\./sites/docs/_build'],
    )

    # Run observer loop
    observer = Observer()
    # TODO: Find parent directory of tasks.py and use that.
    for x in (www_handler, api_handler):
        observer.schedule(x, '.', recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


# TODO: merge w/ invoke's task of same name
@ctask
def sites(c):
    """
    Build both doc sites w/ maxed nitpicking.
    """
    # Turn warnings into errors, emit warnings about missing references.
    # This gives us a maximally noisy docs build.
    # Also enable tracebacks for easier debuggage.
    opts = "-W -n -T"
    # This is super lolzy but we haven't actually tackled nontrivial in-Python
    # task calling yet, so...
    docs_c = Context(config=c.config.clone())
    www_c = Context(config=c.config.clone())
    docs_c.update(**docs.configuration())
    www_c.update(**www.configuration())
    docs['build'](docs_c, opts=opts)
    www['build'](www_c, opts=opts)


# TODO: merge w/ invoke's own such task, using invocations or ?
@ctask(help=test.help)
def integration(c, module=None, runner=None, opts=None):
    """
    Run the integration test suite. May be slow!
    """
    opts = opts or ""
    opts += " --tests=integration/"
    test(c, module, runner, opts)


ns = Collection(
    watch, docs, www, test, coverage, integration, sites, release=packaging,
)
ns.configure({"coverage": {"package": "fabric"}})
