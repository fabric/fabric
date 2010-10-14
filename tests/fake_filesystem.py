import os
import stat
from StringIO import StringIO

import paramiko as ssh


class FakeFile(StringIO):
    def __init__(self, value=None, path=None):
        init = lambda x: StringIO.__init__(self, x)
        if value is None:
            init("")
            ftype = 'dir'
            size = 4096
        else:
            init(value)
            ftype = 'file'
            size = len(value)
        attr = ssh.SFTPAttributes()
        attr.st_mode = {'file': stat.S_IFREG, 'dir': stat.S_IFDIR}[ftype]
        attr.st_size = size
        attr.filename = os.path.basename(path)
        self.attributes = attr

    def __str__(self):
        return self.getvalue()


class FakeFilesystem(dict):
    def __setitem__(self, key, value):
        super(FakeFilesystem, self).__setitem__(key, FakeFile(value, key))
