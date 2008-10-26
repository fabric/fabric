
def production():
    "Primes the deployment procedure to execute against production."
    config.fab_hosts = ['localhost']

def staging():
    "Primes the deployment procedure to execute against staging."
    config.fab_hosts = ['127.0.0.1']

def build():
    "Compiles, builds and packages our project locally."
    local("echo Building project.")

@requires('fab_hosts', provided_by=[production, staging])
#@depends(build)
def deploy():
    "Deploy our project to either production or staging."
    invoke(build)
    #build()
    #put('local-files.zip', 'remote-files.zip')
    local("echo poke")
    sudo("whoami") # the final deployment step.

#
# Things to try out:
#  * fab deploy
#  * fab staging deploy
#  * fab staging build deploy
#  * fab production deploy
#
# ... and notice how the output changes for each of these
#
