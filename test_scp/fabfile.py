from fabric.api import put, get

def cpr():
    'works fine'
    put('./stuff/', '/tmp/stuff/', recursive=True)

def cp():
    'works fine, but needs manual intervention for glob of *'
    put('./stuff/*', '/tmp/', recursive=False)

def rcp():
    '''
    errors, to do this well we would probably need to muck with scp.py, not too
    difficult actually....
    '''
    get('/tmp/stuff/*', './dl/', recursive=False)

def rcp2():
    '''
    works just fine
    '''
    get('/tmp/stuff/d1/*', './dl/', recursive=False)

def rcpr():
    '''
    works like a charm
    '''
    get('/tmp/stuff/', './dl/', recursive=True)
