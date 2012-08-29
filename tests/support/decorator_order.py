from fabric.api import hosts, task


@hosts('whatever')
@task
def foo():
    pass


# There must be at least one unmolested new-style task for the decorator order
# problem to appear.
@task
def caller():
    pass
