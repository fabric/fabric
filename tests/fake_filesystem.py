import os
import stat
from StringIO import StringIO
from types import StringTypes

import ssh


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

    def write(self, value):
        StringIO.write(self, value)
        self.attributes.st_size = len(self.getvalue())

    def close(self):
        """
        Always hold fake files open.
        """
        pass

    def __cmp__(self, other):
        me = str(self) if isinstance(other, StringTypes) else self
        return cmp(me, other)


class FakeFilesystem(dict):
    def __init__(self, d=None):
        # Replicate input dictionary using our custom __setitem__
        d = d or {}
        for key, value in d.iteritems():
            self[key] = value

    def __setitem__(self, key, value):
        if isinstance(value, StringTypes) or value is None:
            value = FakeFile(value, key)
        super(FakeFilesystem, self).__setitem__(key, value)

    def normalize(self, path):
        """
        Normalize relative paths.

        In our case, the "home" directory is just the root, /.

        I expect real servers do this as well but with the user's home
        directory.
        """
        if not path.startswith(os.path.sep):
            path = os.path.join(os.path.sep, path)
        return path

    def __getitem__(self, key):
        return super(FakeFilesystem, self).__getitem__(self.normalize(key))
