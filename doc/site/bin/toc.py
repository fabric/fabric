#!/usr/bin/env python
# encoding: utf-8
"""
toc.py

Implements Confluence-like {toc} macro processing on raw'ish HTML.

Created by Christian Vest Hansen on 2008-11-09.
"""

import re

HEADER_RE = re.compile(
    r'^<[hH](?P<lvl>\d)>(?P<headline>.*)</[hH](?P=lvl)>$', re.M)

NUMB = re.compile(r'\W+')

def _new_subster(headers, maxLvl, minLvl):
    def subster(match):
        lvl = match.group('lvl')
        txt = match.group('headline')
        try:
            lvl = int(lvl)
        except ValueError:
            return match.group(0)
        if minLvl < lvl or lvl < maxLvl:
            return match.group(0)
        anchor = re.sub(NUMB, "_", txt).lower()
        headers.append((lvl, anchor, txt))
        return '<h%s><a name="%s">%s</a></h%s>' % (lvl, anchor, txt, lvl)
    return subster

def _to_html_toc(headers):
    lines = []
    stack = [0]
    for lvl, anchor, headline in headers:
        if stack[-1] < lvl:
            lines.append('<ul>')
            stack.append(lvl)
        while stack[-1] > lvl:
            stack.pop()
            lines.append('</ul>')
        line = '<li><a href="#%s">%s</a></li>' % (anchor, headline)
        lines.append(line)
    for _ in stack[1:]:
        lines.append('</ul>')
    out = '\n'.join(lines)
    return out

def toc(html, maxLvl=2, minLvl=5, count=1):
    """
    This function looks through an HTML doc and will replace a {toc} macro
    with a table-of-contents set of nested lists that matches the header tags.
    """
    if html.find("{toc}") != -1:
        headers = []
        subster = _new_subster(headers, maxLvl, minLvl)
        html = re.sub(HEADER_RE, subster, html)
        html = html.replace("{toc}", _to_html_toc(headers), count)
    return html

