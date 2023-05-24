# flake8: noqa
from ._version import __version_info__, __version__
from .connection import Config, Connection
from .runners import Remote, RemoteShell, Result
from .group import Group, SerialGroup, ThreadingGroup, GroupResult
from .tasks import task, Task
from .executor import Executor

# Best-effort import of module relying on a Paramiko 3.2+ API member
# TODO: this is chiefly a concession to our "v1->v2 shim test" in CI, since
# Fabric 1.x wants Paramiko<3.
try:
    from .auth import OpenSSHAuthStrategy
except ImportError:
    pass
