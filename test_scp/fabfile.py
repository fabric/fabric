from fabric.api import put, get, run, local, runs_once, env
import os
import glob
import filecmp

##################################################
# manual control                                 #
##################################################
def cleanup():
    _cleanup()

##################################################
# Tests of put()                                 #
##################################################
def cpr():
    put('./stuff/', '/tmp/foo/', recursive=True)

def cpr2():
    put('./*[!yc]', "/tmp/foo", recursive=True)

def cpr3():
    put('.', '/tmp/foo', recursive=True)

def cpr4():
    d = os.getcwd()
    put(d, '/tmp/foo', recursive=True)

def cpr5():
    os.chdir('../paramiko')
    put('../test_scp/stuff/', '/tmp/foo', recursive=True)

def cpg():
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
    sdir = os.getcwd()
    os.chdir('/tmp/foo')
    get(os.path.join(sdir,'stuff/f1'), '.', recursive=False)

def rcp2():
    local('touch /tmp/foo/file')
    get(os.path.join(os.getcwd(),'stuff/f1'), '/tmp/foo/file', recursive=False)

def rcp3():
    os.mkdir('/tmp/foo/testdir')
    get(os.path.join(os.getcwd(),'stuff/f1'), '/tmp/foo/testdir', recursive=False)


def rcpg():
    get(os.path.join(os.getcwd(),'stuff/*'), '/tmp/foo', recursive=False)


def rcpr():
    get(os.path.join(os.getcwd(),'stuff/'), '/tmp/foo', recursive=True)

def rcpr2():
    get(os.path.join(os.getcwd(),'*[!yc]'), '/tmp/foo', recursive=True)

##################################################
# helper functions for testall, and testall      #
##################################################
def _cleanup():
    env.warn_only = True
    local('rm -r /tmp/foo/*')
    env.warn_only = False


# this is a global var for config purposes
IGNORE_PATS = ['*.py', '*.pyc', '.*.swp']
def _dircmp(d1, d2, ignore=None, everything = False):
    g = glob.glob
    ign = ignore if ignore else []

    if not everything:
        for x in IGNORE_PATS:
            ign += g(x)

    return _fullcmp(filecmp.dircmp(d1, d2, ign))

def _fullcmp(cmpobj):
    if cmpobj.left_only or cmpobj.right_only:
        return False
    elif len(cmpobj.subdirs):
        return True and all(_fullcmp(it) for it in cmpobj.subdirs.values())
    else:
        return True

def testall():
    sdir = os.getcwd()
    print "CPR"
    _cleanup()
    cpr()
    assert _dircmp('.', '/tmp/foo', ['things']), "CPR"
    os.chdir(sdir)

    print "CPR2"
    _cleanup()
    cpr2()
    assert _dircmp('.', '/tmp/foo', []), "CPR2"
    os.chdir(sdir)

    print "CPR3"
    _cleanup()
    cpr3()
    assert _dircmp('.','/tmp/foo', [], True), "CPR3"
    os.chdir(sdir)

    print "CPR4"
    _cleanup()
    cpr4()
    ign = os.listdir('..')
    ign.remove('test_scp')
    assert _dircmp('..','/tmp/foo', ign), "CPR4"
    os.chdir(sdir)

    print "CPR5"
    _cleanup()
    cpr5()
    os.chdir(sdir)
    assert _dircmp('.', '/tmp/foo', ['things']), "CPR5"

    print "CPG"
    _cleanup()
    cpg()
    assert _dircmp('./stuff/', '/tmp/foo', ['d1']), "CPG"
    os.chdir(sdir)

    print "CP"
    _cleanup()
    cp()
    assert os.path.isfile('/tmp/foo/f1'), "CP"
    os.chdir(sdir)

    print "CP2"
    _cleanup()
    cp2()
    assert filecmp.cmp('./stuff/f1', '/tmp/foo/file',False), "CP2"
    os.chdir(sdir)

    print "RCP"
    _cleanup()
    rcp()
    assert os.path.isfile('./f1'), "RCP"
    os.chdir(sdir)

    print "RCP2"
    _cleanup()
    rcp2()
    assert filecmp.cmp('/tmp/foo/file', os.path.join(sdir,'stuff/f1'),False), "RCP2"
    os.chdir(sdir)

    print "RCP3"
    _cleanup()
    rcp3()
    assert filecmp.cmp('/tmp/foo/testdir/f1', os.path.join(sdir, 'stuff/f1'), False), "RCP3"
    os.chdir(sdir)

    print "RCPG"
    _cleanup()
    rcpg()
    assert _dircmp('./stuff/', '/tmp/foo', ['d1']), "RCPG"
    os.chdir(sdir)

    print "RCPR"
    _cleanup()
    rcpr()
    assert _dircmp('.', '/tmp/foo', ['things']), "RCPR"
    os.chdir(sdir)

    print "RCPR2"
    _cleanup()
    rcpr2()
    assert _dircmp('.', '/tmp/foo', []), "RCPR2"
    os.chdir(sdir)

