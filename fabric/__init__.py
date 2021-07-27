# flake8: noqa
from fabric._version import __version_info__, __version__
from fabric.connection import Config, Connection
from fabric.runners import Remote, RemoteShell, Result
from fabric.group import Group, SerialGroup, ThreadingGroup, GroupResult
from fabric.tasks import task, Task
from fabric.executor import Executor
