
# Our server roles:
rdbms = ['127.0.0.1']
httpd = ['localhost']

def production():
    # this would set `rdbms` and `httpd` to prod. values.
    # for now we just switch them around in order to observe the effect
    global httpd, rdbms
    rdbms, httpd = httpd, rdbms
    # ... except, this dosn't actually work :(

def build():
    local('echo Building project')

@hosts(*rdbms)
def prepare_db():
    run("echo Preparing database for deployment")

@hosts(*httpd)
def prepare_web():
    run("echo Preparing web servers for deployment")

@depends(prepare_db, prepare_web)
@hosts(*httpd)
def deploy():
    run("echo Doing final deployment things to $(fab_host)")
