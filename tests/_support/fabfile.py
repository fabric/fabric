from invoke import task, Context
from fabric import Connection


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
def expect_vanilla_Context(c):
    assert isinstance(c, Context)
    assert not isinstance(c, Connection)


@task
def expect_from_env(c):
    assert c.config.run.echo is True


@task
def expect_mutation_to_fail(c):
    # If user level config changes are preserved between parameterized per-host
    # task calls, this would assert on subsequent invocations...
    assert "foo" not in c.config
    # ... because of this:
    c.config.foo = "bar"


@task
def mutate(c):
    c.foo = "bar"


@task
def expect_mutation(c):
    assert c.foo == "bar"


@task
def expect_identity(c):
    assert c.config.connect_kwargs["key_filename"] == ["identity.key"]


@task
def expect_identities(c):
    assert c.config.connect_kwargs["key_filename"] == [
        "identity.key",
        "identity2.key",
    ]


@task
def first(c):
    print("First!")


@task
def third(c):
    print("Third!")


@task(pre=[first], post=[third])
def second(c, show_host=False):
    if show_host:
        print("Second: {}".format(c.host))
    else:
        print("Second!")
