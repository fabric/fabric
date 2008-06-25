
# fabfile.py - A fabfile for Fabric itself.
# Copyright (C) 2008  Christian Vest Hansen
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

set(
    nongnu_user = 'karmazilla',
)

def clean(**kwargs):
    "Recurse the directory tree and remove all files matched by .gitignore."
    # passing -delete to find doesn't work for directories, hence xargs rm -r
    local('cat .gitignore | xargs -I PATTERN '
        + 'find . -name PATTERN -not -path "./.git/*" | (xargs rm -r || true)')
    if not "nogc" in kwargs:
        local('git gc --prune')

def ready_files():
    local('mkdir dist')
    set(prefix='fab-%(fab_version)s', filename='dist/%(prefix)s.tar.gz')
    # This next part needs explaining...
    # 1. use Git to pack HEAD in TAR format to stdout, so we don't distribute
    #    files with local changes. Plus, make sure that Git only packs those
    #    files that are named in MANIFEST, so that we make sure that the
    #    packages in the CheeseShop (PyPi) and on nongnu.org are similar.
    # 2. Then we pipe the TAR data through gzip so we get it in tar.gz format.
    # 3. Then, in the dist directory, we BOTH write data to a tar.gz file, AND
    #    unpack it. This will create a clean-room file-set that we can use for
    #    running distutils. This way, we also make sure that we don't get
    #    uncommittet changes in our distutils package.
    # Pretty clever, eh? Unix CLI-fu!
    local('git archive --format=tar --prefix=%(prefix)s/ HEAD '
            + '$(cat MANIFEST | perl -p -e "s/\\n/ /") | gzip | '
            + '(cd dist && tee %(prefix)s.tar.gz | tar xzf -)')
    local('gpg -b --use-agent %(filename)s')

def release(**kwargs):
    "Create a new release of Fabric, and upload it to our various services."
    dry = 'dry' in kvargs
    if not dry:
        local('git tag -s -m "Fabric v. %(fab_version)s" %(fab_version)s HEAD')
    ready_files()
    scp_cmd = 'scp $(filename) $(nongnu_user)@dl.sv.nongnu.org:/releases/fab/'
    if not dry:
        local(scp_cmd)
        set(filename='%(filename)s.sig')
        local(scp_cmd)
    distutil_cmd = ('cd dist/%(prefix)s/ && '
        + 'python setup.py sdist upload --sign')
    if dry:
        distutil_cmd += ' --dry-run'
    local(distutil_cmd)
    upload_website()

def install(**kwargs):
    "Install Fabric locally."
    if 'notest' not in kvargs:
        test()
    local('python setup.py build')
    local('sudo python setup.py install')

def layout(**kvwrgs):
    """
    Print a layout-overview of fabric.py to the console.
    
    Optionally append an argument to the underlying grep call.
    
    Examples:
        fab layout
        fab layout:-n
        fab layout:-n,--color=always
    
    """
    options = ' '.join(['='.join(filter(None,i)) for i in kvargs.items()])
    local(r'grep %s \\\(^#\ .*:$\\\)\\\|.*def\ .* fabric.py|' % options
            + 'perl -p -e "s/def /   def /"')

def test():
    "Run all unit tests."
    local("cd test && ./gen_tests.py")
    local("python test/alltests.pyt")

def website():
    "Generates the Fabric website."
    local("cd doc/site && ./generate.py")

def upload_website():
    "Generates and uploads the Fabric website to nongnu.org"
    local("cd doc/site && export CVS_RSH=ssh && "
        + "cvs -z3 -d:ext:$(nongnu_user)@cvs.sv.gnu.org:/webcvs/fab co fab")
    website()
    prompt('website_commit_msg', 'Website commit message',
        default = 'Website for version $(fab_version)')
    local("cd doc/site/fab && export CVS_RSH=ssh && "
        + "cvs commit -m '$(website_commit_msg)'")
