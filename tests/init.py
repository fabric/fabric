from spec import Spec, eq_, ok_

import fabric
from fabric import _version, connection, transfer


class init(Spec):
    "__init__"
    def version_and_version_info(self):
        for name in ('__version_info__', '__version__'):
            eq_(getattr(_version, name), getattr(fabric, name))

    def Connection(self):
        ok_(fabric.Connection is connection.Connection)

    def Group(self):
        ok_(fabric.Group is connection.Group)

    def Transfer(self):
        ok_(fabric.Transfer is transfer.Transfer)
