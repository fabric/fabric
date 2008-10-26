
# Our server roles:
rdbms = ['127.0.0.1']
httpd = ['localhost']

def production():
    # this would set `rdbms` and `httpd` to prod. values.
    pass

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
    run("echo Doing final deployment things")
