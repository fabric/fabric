
def test_local_failures():
    local('false 1', fail='ignore')
    local('false 2', fail='warn')
    local('echo must print')
    local('false 3') # default fail is abort
    local('echo must NOT print')

def test_remote_failures(**kwargs):
    set(fab_hosts = ['127.0.0.1', 'localhost'])
    exc = run
    if 'sudo' in kwargs:
        exc = sudo
    
    exc('false 1', fail='ignore')
    exc('false 2', fail='warn')
    exc('echo must print')
    exc('false 3') # default fail is abort
    exc('echo must NOT print')
