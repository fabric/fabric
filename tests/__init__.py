from fabric.api import env
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


def setup():
    global thread, all_done
    port = 2200
    env.host_string = 'localhost:%s' % port 
    env.disable_known_hosts = True
    env.password = 'anything'

    thread, all_done = serve_responses(responses, port)


def teardown():
    global thread, all_done
    all_done.set()
    thread.join()
