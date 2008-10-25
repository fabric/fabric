
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

def test_prompting():
    # Simplest form:
    prompt('environment', 'Please specify target environment')
    
    # With default:
    prompt('dish', 'Specify favorite dish', default='spam & eggs')
    
    # With validation, i.e. require integer input:
    prompt('nice', 'Please specify process nice level', validate=int)
    
    # With validation against a regular expression:
    prompt('release', 'Please supply a release name',
            validate=r'^\w+-\d+(\.\d+)?$')

def hello():
    local("echo hello")

@hosts('localhost')
def test_nested_remotes_part_2():
    "used by test_nested_remotes"
    run("echo 2-5 $(fab_host)")

# this won't connect to 127.0.0.1 when called by test_nested_remotes()!
@hosts('localhost', '127.0.0.1')
def test_nested_remotes_part_4():
    "used by test_nested_remotes"
    run("echo 4-5 $(fab_host)")

@hosts('localhost')
def test_nested_remotes():
    "Tests nesting of commands that require connections."
    run("echo 1-5")
    test_nested_remotes_part_2()
    run("echo 3-5")
    test_nested_remotes_part_4()
    run("echo 5-5 and done.")

_protected = "Yes!"
def test_protected_names():
    print "Do we have access to _protected names?", _protected
