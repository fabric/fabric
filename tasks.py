from os.path import join
import sys
import time

from invocations import docs as _docs
from invocations.testing import test

from invoke import Collection, Context, ctask


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

# TODO: merge w/ invoke's own such task, using invocations or ?
@ctask(help=test.help)
def integration(c, module=None, runner=None, opts=None):
    """
    Run the integration test suite. May be slow!
    """
    opts = opts or ""
    opts += " --tests=integration/"
    test(c, module, runner, opts)


ns = Collection(watch, docs=docs, www=www, test=test, integration=integration)
