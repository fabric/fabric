from invoke import task


@task
def build(c):
    pass


@task
def deploy(c):
    pass


@task
def basic_run(c):
    c.run("nope")


@task
def expect_mutation_to_fail(c):
    # If user level config changes are preserved between parameterized per-host
    # task calls, this would assert on subsequent invocations...
    assert 'foo' not in c.config
    # ... because of this:
    c.config.foo = 'bar'


