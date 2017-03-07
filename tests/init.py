from spec import Spec, eq_, ok_

import fabric
from fabric import _version, connection


class init(Spec):
    "__init__"
    def version_and_version_info(self):
        for name in ('__version_info__', '__version__'):
            eq_(getattr(_version, name), getattr(fabric, name))

    def Connection(self):
        ok_(fabric.Connection is connection.Connection)

    def Group(self):
        ok_(fabric.Group is connection.Group)

    def SerialGroup(self):
        ok_(fabric.SerialGroup is connection.SerialGroup)

    def ThreadingGroup(self):
        ok_(fabric.ThreadingGroup is connection.ThreadingGroup)

    def Config(self):
        ok_(fabric.Config is connection.Config)
