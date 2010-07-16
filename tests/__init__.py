from threading import Event

from fabric.api import env
from fabric.network import interpret_host_string

from server import serve_responses


thread, all_done = None, None

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
    'jforcier': 'jforcier'
}


def setup():
    global thread, all_done
    port = 2200
    interpret_host_string('jforcier@localhost:%s' % port)
    env.disable_known_hosts = True
    env.password = users['jforcier']
    # Threading event added to env (so that the tests, within our thread, may
    # manipulate it) and passed into the server thread (so it can also see the
    # value)
    env.use_pubkeys = Event()
    env.use_pubkeys.set()
    thread, all_done = serve_responses(responses, users, port, env.use_pubkeys)


def teardown():
    global thread, all_done
    all_done.set()
    thread.join()
