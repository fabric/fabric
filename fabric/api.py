"""
Non-init module for doing convenient * imports from.

Necessary because if we did this in __init__, one would be unable to import
anything else inside the package -- like, say, the version number used in
setup.py -- without triggering loads of most of the code. Which doesn't work so
well when you're using setup.py to install e.g. paramiko!
"""
from context_managers import setenv, settings, show, hide
from decorators import hosts, roles, runs_once
from operations import require, prompt, put, get, run, sudo, local
from state import env
from utils import abort, warn
