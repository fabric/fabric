"""
Non-init module for doing convenient * imports from.

Necessary because if we did this in __init__, one would be unable to import
anything else inside the package -- like, say, the version number used in
setup.py -- without triggering loads of most of the code. Which doesn't work so
well when you're using setup.py to install e.g. paramiko!
"""
from fapric.context_managers import cd, hide, settings, show, path, prefix, lcd
from fapric.decorators import hosts, roles, runs_once, with_settings, task
from fapric.operations import (require, prompt, put, get, run, sudo, local,
    reboot, open_shell)
from fapric.state import env, output
from fapric.utils import abort, warn, puts, fastprint
