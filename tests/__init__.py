from threading import Event

from fabric.api import env
from fabric.network import interpret_host_string
from fabric.thread_handling import ThreadHandler

from server import serve_responses


server, server_worker = None, None

responses = {
    "ls /simple": "some output",
    "ls /": """AUTHORS
FAQ
Fabric.egg-info
INSTALL
LICENSE
MANIFEST
README
build
docs
fabfile.py
fabfile.pyc
fabric
requirements.txt
setup.py
tests"""
}

users = {
    'root': 'root',
    env.local_user: 'password'
}


def setup():
    global server, server_worker
    port = 2200
    # Setup environment
    interpret_host_string('%s@localhost:%s' % (env.local_user, port))
    env.disable_known_hosts = True
    env.password = users[env.local_user]
    # Threading events to control server processes from teardown() or test code
    env.use_pubkeys = Event()
    env.use_pubkeys.set()
    server = serve_responses(responses, users, port, env.use_pubkeys)
    server.all_done = Event()
    server_worker = ThreadHandler('server', server.serve_forever)

def teardown():
    global server, server_worker
    server.all_done.set()
    server.shutdown()
    server_worker.thread.join()
    e = server_worker.exception
    if e:
        raise e[0], e[1], e[2]
