from fabric import task


@task
def expect_conf_value(c):
    assert c.it_came_from == "yml"


@task
def expect_conf_key_filename(c):
    expected = ["private.key", "other.key"]
    got = c.connect_kwargs.key_filename
    assert got == expected, "{!r} != {!r}".format(got, expected)


@task
def expect_cli_key_filename(c):
    expected = ["cli.key"]
    got = c.connect_kwargs.key_filename
    assert got == expected, "{!r} != {!r}".format(got, expected)
