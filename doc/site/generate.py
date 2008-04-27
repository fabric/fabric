#!/usr/bin/env python

# generate.py, part of:
#   Fabric - Pythonic remote deployment tool.
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

import os
from os.path import exists, abspath
from glob import glob
from textile import textile

OUTDIR = "fab"

def generate():
    "Generates a web site from a directory full of textile .txt files."
    if not exists(OUTDIR):
        os.mkdir(OUTDIR)
    files = glob('*.txt')
    template_file = open('template.html', 'r')
    template = template_file.read()
    template_file.close()
    for filename in files:
        print "Processing", filename
        name, _, _ = filename.rpartition('.')
        infile = open(filename, 'r')
        outfile = open(OUTDIR + "/" + name + '.html', 'w')
        outfile.write(template % {
            "name" : name,
            "content" : textile(infile.read()).replace('<br />', ''),
        })
        infile.close()
        outfile.close()

def move_other_files():
    file_list_file = open('other-files', 'r')
    file_list = filter(exists, map(str.strip, file_list_file))
    file_list_file.close()
    for filename in file_list:
        src = abspath(filename)
        dst = abspath(OUTDIR + "/" + filename)
        if exists(dst):
            os.remove(dst)
        os.symlink(src, dst)

if __name__ == '__main__':
    generate()
    move_other_files()

