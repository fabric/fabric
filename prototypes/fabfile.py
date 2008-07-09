
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


import datetime
from StringIO import StringIO
re = __import__('re')
global_variables_are_available = True

def test_imports():
    assert datetime is not None
    assert StringIO is not None
    assert re is not None
    global global_variables_are_available
    assert global_variables_are_available
    global_variables_are_available = 1
    local("echo all good.")
    set(test_imports_has_run=True)

def test_global_assignment():
    require('test_imports_has_run', provided_by=[test_imports])
    global global_variables_are_available
    assert global_variables_are_available == 1
    local("echo all double-good.")
