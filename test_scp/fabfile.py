from fabric.api import put, get, run, local, runs_once, env
import os

##################################################
# admin stuff                                    #
##################################################
@runs_once
def clean(dname='./*'):
    env.warn_only = True
    local('rm -r ' + dname)
    env.warn_only = False

##################################################
# Tests of put()                                 #
##################################################
def cpr():
    'works fine'
    put('./stuff/', '/tmp/foo/', recursive=True)

def cpr2():
    put('./*[!py]', "/tmp/foo", recursive=True)

def cpr3():
    put('.', '/tmp/foo', recursive=True)

def cpr4():
    d = os.getcwd()
    put(d, '/tmp/foo', recursive=True)

def cpr5():
    os.chdir('../paramiko')
    put('../test_scp/stuff/', '/tmp/foo', recursive=True)

def cpg():
    'works fine, but needs manual intervention for glob of *'
    put('./stuff/*', '/tmp/foo', recursive=False)


def cp():
    put('./stuff/f1','/tmp/foo/',recursive=False)

def cp2():
    run('touch /tmp/foo/file')
    put('./stuff/f1','/tmp/foo/file',recursive=False)

##################################################
# Tests of get()                                 #
##################################################
def rcp():
    get('/tmp/foo/stuff/f1', './f1')

def rcp2():
    local('touch ./file')
    get('/tmp/foo/stuff/f1', './file')

def rcp3():
    os.mkdir('testdir')
    get('/tmp/foo/stuff/f1', 'testdir')


def rcpg():
    get('/tmp/foo/stuff/*', '.', recursive=False)


def rcpr():
    get('/tmp/foo/stuff/', '.', recursive=True)

def rcpr2():
    get('/tmp/foo/*[!py]', '.', recursive=True)

