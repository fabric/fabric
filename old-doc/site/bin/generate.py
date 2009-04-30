#!/usr/bin/env python

import os
from os.path import exists, abspath
from glob import glob
from StringIO import StringIO
from textile import textile
from markdown2 import markdown
from toc import toc

try:
    import pygments
except ImportError:
    print "Warning: Pygments is required for Markdown code coloring."
try:
    from twisted.python import htmlizer
except ImportError:
    print "Warning: Twisted is required for Textile code coloring."

OUTDIR = "fab"

def textile_format(txt, _=None):
    out = textile(txt).replace('<br />', '')
    out = toc(out)
    return out

def markdown_format(mkd, _=None):
    out = markdown(mkd, extras=['code-friendly', 'code-color'])
    out = out.replace(u'<pre><code>', u'<pre><code>\n')
    out = out.replace(u'</code></pre>', u'\n</code></pre>')
    out = toc(out)
    return out

def python_script_output(src, filename):
    out = StringIO()
    script = compile(src, filename, "exec")
    eval(script, {'out': out})
    return toc(out.getvalue())

FORMATS = {
    'txt': textile_format,
    'textile': textile_format,
    'markdown': markdown_format,
    'md': markdown_format,
    'py': python_script_output,
}

def generate():
    "Generates a web site from a directory full of textile and markdown files."
    if not exists(OUTDIR):
        os.mkdir(OUTDIR)
    files = []
    for suffix in FORMATS.keys():
        files += glob('*.' + suffix)
    template_file = open('template.html', 'r')
    template = template_file.read()
    template_file.close()
    for filename in files:
        print "Processing", filename
        name, _, suffix = filename.rpartition('.')
        convert = FORMATS[suffix]
        infile = open(filename, 'r')
        intext = infile.read()
        try:
            content = convert(intext.decode('utf-8'), filename)
        except UnicodeDecodeError:
            # Textile seems unable to handle unicode.
            content = convert(intext, filename)
        output = template % {
            u"name" : name,
            u"content" : content,
        }
        outfile = open(OUTDIR + "/" + name + '.html', 'wb')
        outfile.write(output.encode('utf-8'))
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

