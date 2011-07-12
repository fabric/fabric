from fabric.api import task

@task(aliases=["foo_aliased", "foo_aliased_two"])
def foo():
    pass
