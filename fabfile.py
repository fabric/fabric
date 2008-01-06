
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

def clean():
    "Recurse the directory tree and remove all files matched by .gitignore."
    # passing -delete to find doesn't work for directories, hence xargs rm -r
    local('cat .gitignore | xargs -I PATTERN '
        + 'find . -name PATTERN -not -path "./.git/*" | xargs rm -r')

def release():
    "Create a new release of Fabric, and upload it to our various services."
    set('prefix', 'fab-%(fab_version)s')
    local('git tag -s -m "Fabric v. %(fab_version)s" %(fab_version)s HEAD')
    local('git archive --format=tar --prefix=%(prefix)s '
        + '%(fab_version)s | gzip >%(prefix)s.tar.gz')
    
