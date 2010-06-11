from fabric.state import output, connections, env
import stat
import os
from fnmatch import filter as fnfilter

class FabSFTP(object):
    def __init__(self, hoststr):
        self.ftp = connections[hoststr].open_sftp()
        self.host_string = hoststr

    # remember __getattr__ is only called if python cant find "attr" in
    # __dict__ -- so this is pretty safe, even with same-named things
    def __getattr__(self, attr):
        return getattr(self.ftp, attr)

    def isdir(self, path):
        try:
            return stat.S_ISDIR(self.ftp.lstat(path).st_mode)
        except IOError:
            return False

    def islink(self, path):
        try:
            return stat.S_ISLNK(self.ftp.lstat(path).st_mode)
        except IOError:
            return False

    def exists(self, path):
        try:
            self.ftp.lstat(path).st_mode
        except IOError:
            return False
        return True

    def glob(self, pat):
        dirpart, pat = os.path.split(pat)
        rlist = self.ftp.listdir(dirpart)

        #print "rlist is", rlist
        names = fnfilter([f for f in rlist if not f[0] == '.'], pat)
        if len(names):
            return [os.path.join(dirpart, name) for name in names]
        else:
            return [dirpart]

    def walk(self, top, topdown=True, onerror=None, followlinks=False):
        from os.path import join, isdir, islink

        # We may not have read permission for top, in which case we can't
        # get a list of the files the directory contains.  os.path.walk
        # always suppressed the exception then, rather than blow up for a
        # minor reason when (say) a thousand readable directories are still
        # left to visit.  That logic is copied here.
        try:
            # Note that listdir and error are globals in this module due
            # to earlier import-*.
            names = self.ftp.listdir(top)
        except Exception, err:
            if onerror is not None:
                onerror(err)
            return

        dirs, nondirs = [], []
        for name in names:
            if self.isdir(join(top, name)):
                dirs.append(name)
            else:
                nondirs.append(name)

        if topdown:
            yield top, dirs, nondirs

        for name in dirs:
            path = join(top, name)
            if followlinks or not self.islink(path):
                for x in self.walk(path, topdown, onerror, followlinks):
                    yield x
        if not topdown:
            yield top, dirs, nondirs

    def get(self, rpath, lpath):
        if os.path.isdir(lpath):
            lpath = os.path.join(lpath, os.path.basename(rpath))
        if output.running:
            #print("[%s] download: %s <- %s" % (
                env.host_string, lpath, rpath
            ))
        # Handle any raised exceptions (no return code to inspect here)
        self.ftp.get(rpath, lpath)

    def get_dir(self, rpath, lpath):
        if os.path.basename(rpath):
            strip = os.path.dirname(rpath)
        else:
            strip = os.path.dirname(os.path.dirname(rpath))

        #print 'rpath is', rpath ,'strip is', strip
        for context, dirs, files in self.walk(rpath):
            #print 'context is', context,
            lcontext = context.replace(strip,'')
            lcontext = lcontext.lstrip('/')
            lcontext = os.path.join(lpath, lcontext)
            #print "lcontext is", lcontext

            if not os.path.exists(lcontext):
                os.mkdir(lcontext)
            for d in dirs:
                n = os.path.join(lcontext, d)
                if not os.path.exists(n):
                    os.mkdir(n)
            for f in files:
                rpath = os.path.join(context, f)
                n = os.path.join(lcontext, f)
                self.get(rpath, n)

    def put(self, lpath, rpath):
        pre = self.ftp.getcwd()
        pre = pre if pre else ''

        if self.isdir(rpath):
            rpath = os.path.join(rpath, os.path.basename(lpath))
        if output.running:
            #print 'lpath:', lpath, 'rpath:',rpath,'pre:', pre
            print("[%s] put: %s -> %s" % (
                env.host_string, lpath, os.path.join(pre, rpath)
            ))
        # Try to catch raised exceptions (which is the only way to tell if
        # this operation had problems; there's no return code) during upload
        # Actually do the upload
        rattrs = self.ftp.put(lpath, rpath)
        # and finally set the file mode
        lmode = os.stat(lpath).st_mode
        if lmode != rattrs.st_mode:
            self.ftp.chmod(rpath, lmode)

    def put_dir(self, lpath, rpath):
        if os.path.basename(lpath):
            strip = os.path.dirname(lpath)
        else:
            strip = os.path.dirname(os.path.dirname(lpath))

        #print 'lpath is', lpath, 'strip is',strip
        for context, dirs, files in os.walk(lpath):
            rcontext = context.replace(strip,'')
            rcontext = rcontext.lstrip('/')
            #print "rcontext is", rcontext,
            rcontext = os.path.join(rpath, rcontext)
            #print 'then ', rcontext

            if not self.exists(rcontext):
                self.ftp.mkdir(rcontext)

            for d in dirs:
                n = os.path.join(rcontext,d)
                if not self.exists(n):
                    self.ftp.mkdir(n)

            for f in files:
                lpath = os.path.join(context,f)
                n = os.path.join(rcontext,f)
                self.put(lpath, n)
