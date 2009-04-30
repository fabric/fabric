
def test():
    config.x = 'a'
    config.var = '$(x)'
    # Be cautioned that the standard Python %s syntax cannot be predictably
    # escaped because of the recursive nature of _lazy_format().
    # I recommend using the Fabric $() syntax whenever possible.
    config.cmd = "echo '%%(var)s is %(var)s and \$(var) is $(var)'"
    config.var = 'b'
    local(config.cmd)

def test2():
    config.y = 'y'
    config.z = 'z'
    local("echo x$(y)$(z)")

config.fab_print_real_sudo = True
@hosts('localhost')
def bash():
    run("echo \\\$poke; whoami")
    sudo("echo \\\$poke; whoami")
    sudo("whoami")

