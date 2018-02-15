from fabric import task


@task
def expect_connect_kwarg(c, key, val):
    assert c.config.connect_kwargs[key] == val
