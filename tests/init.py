from spec import Spec, eq_, ok_

import fabric
from fabric import _version, connection, runners, group


class init(Spec):
    "__init__"
    def version_and_version_info(self):
        for name in ('__version_info__', '__version__'):
            eq_(getattr(_version, name), getattr(fabric, name))

    def Connection(self):
        ok_(fabric.Connection is connection.Connection)

    def Result(self):
        ok_(fabric.Result is runners.Result)

    def Config(self):
        ok_(fabric.Config is connection.Config)

    def Group(self):
        ok_(fabric.Group is group.Group)

    def SerialGroup(self):
        ok_(fabric.SerialGroup is group.SerialGroup)

    def ThreadingGroup(self):
        ok_(fabric.ThreadingGroup is group.ThreadingGroup)

    def GroupResult(self):
        ok_(fabric.GroupResult is group.GroupResult)
