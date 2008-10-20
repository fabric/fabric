"""
api.py - generates the content of the api.html page on the website.

Not to be run directly, but rather compiled and executed by bin/generate.py
"""

import fabric
from markdown2 import markdown
from datetime import datetime

#
# Helper functions
#
def header(lvl, txt):
    out.write("<h%d>%s</h%d>\n" % (lvl, txt, lvl))

def anchor(section_name, item_name):
    return "%s_%s" % (section_name.lower(), item_name)

def summary(name, obj, sect_name):
    doc = obj.__doc__
    out.write('<li><a href="#%s">' % anchor(sect_name, name))
    out.write(name)
    out.write("</a>")
    if doc:
        out.write(": ")
        out.write(filter(None, map(str.strip, doc.splitlines()))[0])
    out.write("</li>\n")

def full_description(name, obj, sect_name):
    out.write('<p><a name="%s"><strong>' % anchor(sect_name, name))
    out.write(name) # note: arg-specs makes no sense here, so aren't written.
    out.write(".</strong></a></p>\n")
    out.write("<blockquote>\n")
    doc = obj.__doc__
    if doc:
        doc = doc.strip()
        doc_lines = doc.splitlines()
        def fix_indent(txt):
            if txt.startswith('    '):
                return txt[4:]
            return txt
        doc_lines = map(fix_indent, doc_lines)
        doc = '\n'.join(doc_lines)
        out.write(markdown(doc, extras=['code-friendly']))
    else:
        out.write("<p><em>No description.</em></p>\n")
    out.write("</blockquote>\n")

def as_list(name, fn):
    out.write("<ul>\n")
    if name:
        out.write("<li><strong>%s</strong>\n" % name)
        out.write("<ul>\n")
    fn()
    if name:
        out.write("</ul></li>\n")
    out.write("</ul>\n")

def as_sections(name, fn):
    if name:
        header(2, name)
    fn()

def write_section(section_name, form_fn, printable):
    items = printable.items()
    items.sort()
    for name, obj in items:
        form_fn(name, obj, section_name)

def render(doc, section_wrapper, item_printer):
    for name, items in doc:
        write_section_items = lambda: write_section(name, item_printer, items)
        section_wrapper(name, write_section_items)

def write_document(layout):
    header(2, "Table of Contents")
    render(layout, as_list, summary)
    out.write("<hr/>\n")
    render(layout, as_sections, full_description)

#
# Main() code goes here
#
header(1, "Fabric API specification")

out.write("""
<p>
    This document lists all the commands, operations and strategies that are
    available to fabfiles.
</p>
<p>
    This document was automatically generated for Fabric version %s on %s.
</p>
""" % (fabric.__version__, datetime.now().strftime("%A, %d of %B, %Y")))

write_document([
    ('Commands', fabric.COMMANDS),
    ('Operations', fabric.OPERATIONS),
    ('Strategies', fabric.STRATEGIES),
])

