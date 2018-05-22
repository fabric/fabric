from fabric import task


@task
def runtime_ssh_config(c):
    # NOTE: assumes it's run with host='runtime' + ssh_configs/runtime.conf
    # TODO: SSHConfig should really learn to turn certain things into ints
    # automatically...
    assert c.ssh_config["port"] == "666"
    assert c.port == 666


@task
def dummy(c):
    pass
