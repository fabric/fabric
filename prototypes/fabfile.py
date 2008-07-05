
def test_local_failures():
    local('false 1', fail='ignore')
    local('false 2', fail='warn')
    local('echo must print')
    local('false 3') # default fail is abort
    local('echo must NOT print')

def test_remote_failures():
    set(fab_hosts = ['127.0.0.1', 'localhost'])
    run('false 1', fail='ignore')
    run('false 2', fail='warn')
    run('echo must print')
    run('false 3') # default fail is abort
    run('echo must NOT print')
