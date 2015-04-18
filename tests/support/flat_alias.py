from swatch.api import task

@task(alias="foo_aliased")
def foo():
    pass
