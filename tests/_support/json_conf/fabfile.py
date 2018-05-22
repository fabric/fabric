from fabric import task


@task
def expect_conf_value(c):
    assert c.it_came_from == "json"
