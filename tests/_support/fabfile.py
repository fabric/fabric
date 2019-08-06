from invoke import Context, task as invtask
from fabric import task, Connection


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
def expect_connect_timeout(c):
    assert c.config.connect_kwargs["timeout"] == 5


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


@task(hosts=["myhost"])
def hosts_are_myhost(c):
    c.run("nope")


@task(hosts=["host1", "host2"])
def two_hosts(c):
    c.run("nope")


@task(hosts=["someuser@host1:1234"])
def hosts_are_host_stringlike(c):
    c.run("nope")


@task(hosts=["admin@host1", {"host": "host2"}])
def hosts_are_mixed_values(c):
    c.run("nope")


@task(hosts=[{"host": "host1", "user": "admin"}, {"host": "host2"}])
def hosts_are_init_kwargs(c):
    c.run("nope")


@invtask
def vanilla_Task_works_ok(c):
    assert isinstance(c, Context)
    assert not isinstance(c, Connection)
