from fabric.api import task, hosts, roles # flake8: noqa


@hosts('whatever')
@task
def foo():
    pass

# There must be at least one unmolested new-style task for the decorator order
# problem to appear.


@task
def caller():
    pass
