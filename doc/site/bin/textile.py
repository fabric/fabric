#!/usr/bin/env python
# _*_ coding: latin1 _*_

"""This is Textile
A Humane Web Text Generator

TODO:
* Make it work with Python 2.1.
* Make it work with Python 1.5.2? Or that's too optimistic?

---
To get an overview of all PyTextile's features, simply
type 'tell me about textile.' in a single line.
"""

__authors__ = ["Roberto A. F. De Almeida (roberto@dealmeida.net)",
               "Mark Pilgrim (f8dy@diveintomark.org)"]
__version__ = "2.0.10"
__date__ = "2004/10/06"
__copyright__ = """
Copyright (c) 2004, Roberto A. F. De Almeida, http://dealmeida.net/
Copyright (c) 2003, Mark Pilgrim, http://diveintomark.org/
All rights reserved.

Original PHP version:
Version 1.0
21 Feb, 2003

Copyright (c) 2003, Dean Allen, www.textism.com
All rights reserved.

Parts of the documentation and some of the regular expressions are (c) Brad
Choate, http://bradchoate.com/. Thanks, Brad!
"""
__license__ = """
Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, 
  this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name Textile nor the names of its contributors may be used to
  endorse or promote products derived from this software without specific
  prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE 
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""
__history__ = """
1.0 - 2003/03/19 - MAP - initial release
1.01 - 2003/03/19 - MAP - don't strip whitespace within <pre> tags;
  map high-bit ASCII to HTML numeric entities
1.02 - 2003/03/19 - MAP - changed hyperlink qtag expression to only
  match valid URL characters (per RFC 2396); fixed preg_replace to
  not match across line breaks (solves lots of problems with
  mistakenly matching overlapping inline markup); fixed whitespace
  stripping to only strip whitespace from beginning and end of lines,
  not immediately before and after HTML tags.
1.03 - 2003/03/20 - MAP - changed hyperlink qtag again to more
  closely match original Textile (fixes problems with links
  immediately followed by punctuation -- somewhere Dean is
  grinning right now); handle curly apostrophe with "ve"
  contraction; clean up empty titles at end.
1.04 - 2003/03/23 - MAP - lstrip input to deal with extra spaces at
  beginning of first line; tweaked list loop to handle consecutive lists
1.1 - 2003/06/06 - MAP - created initial test suite for links and images,
  and fixed a bunch of related bugs to pass them
1.11 - 2003/07/20 - CL - don't demoronise unicode strings; handle
  "they're" properly
1.12 - 2003/07/23 - GW - print debug messages to stderr; handle bq(cite).
1.13 - 2003/07/23 - MAP - wrap bq. text in <p>...</p>
2 - 2004/03/26 - RAFA - rewritten from (almost) scratch to include
  all features from Textile 2 and a little bit more.
2.0.1 - 2004/04/02 - RAFA - Fixed validating function that uses uTidyLib.
2.0.2 - 2004/04/02 - RAFA - Fixed problem with caps letters in URLs.
2.0.3 - 2004/04/19 - RAFA - Multiple classes are allowed, thanks to Dave
  Anderson. The "lang" attribute is now removed from <code>, to be valid
  XHTML. Fixed <span class="caps">UCAS</span> problem.
2.0.4 - 2004/05/20 - RAFA, CLB - Added inline formatting to table cells.
  Curt Bergmann fixed a bug with the colspan formatting. Added Amazon
  Associated id.
2.0.5 - 2004/06/01 - CL - Applied patch from Chris Lawrence to (1) fix
  that Amazon associates ID was being added to all search URIs, (2)
  customize the Amazon site used with the AMAZON variable, and (3) added
  an "isbn" URI type that links directly to an Amazon product by ISBN or
  Amazon ASIN.
2.0.6 - 2004/06/02 - RAFA - Fixed CAPS problem, again. I hope this is
  the last time.
2.0.7 - 2004/06/04 - RAFA, MW - Fixed bullet macro, thanks to Adam
  Messinger. Added patch from Michal Wallace changing {}.pop() for
  compatibility with Python 2.2.x.
2.0.8 - 2004/06/25 - RAFA - Strip tags when adding the content from a
  footnote to the reference link. Escaped '<' and '>' in the self-
  generated documentation.
2.0.9 - 2004/10/04 - RAFA - In images, if ALT is not defined, add an
  empty attribute. Added "LaTeX" style open/close quotes. Fixed a bug 
  where the acronym definition was being formatted with inline rules. 
  Handle "broken" lines correctly, removing the <br /> from inside
  split HTML tags.
2.0.10 - 2004/10/06 - RAFA, LO - Escape all non-escaped ampersands.
  Applied "trivial patch" from Ludvig Omholt to remove newline right
  after the <pre> tag.
"""

# Set your encoding here.
ENCODING = 'latin-1'

# Output? Non-ASCII characters will be automatically
# converted to XML entities if you choose ASCII.
OUTPUT = 'ascii'

# PyTextile can optionally validate the generated
# XHTML code. We can use either mxTidy or uTidyLib.
# You can change the default behaviour here.
VALIDATE = 0

# If you want h1. to be translated to something other
# than <h1>, change this offset. You can also pass it
# as an argument to textile().
HEAD_OFFSET = 0

# If you want to use itex2mml, specify the full path
# to the binary here. You can download it from here:
# http://golem.ph.utexas.edu/~distler/blog/files/itexToMML.tar.gz
itex2mml = None
#itex2mml = '/usr/local/bin/itex2MML'
#itex2mml = '/usr/people/almeida/bin/itex2MML'

# PyTextile can optionally sanitize the generated XHTML,
# which is good for weblog comments or if you don't trust
# yourself.
SANITIZE = 0

# Turn debug on?
DEBUGLEVEL = 0

# Amazon associate for links: "keywords":amazon
# If you don't have one, please consider leaving mine here as
# a small compensation for writing PyTextile. It's commented
# off as default.
#amazon_associate_id = 'bomtempo-21'
amazon_associate_id = None 

#AMAZON = 'www.amazon.co.uk'
AMAZON = 'www.amazon.com'

import re
import sys
import os
import sgmllib
import unicodedata


def _in_tag(text, tag):
    """Extracts text from inside a tag.

    This function extracts the text from inside a given tag.
    It's useful to get the text between <body></body> or
    <pre></pre> when using the validators or the colorizer.
    """
    if text.count('<%s' % tag):
        text = text.split('<%s' % tag, 1)[1]
        if text.count('>'):
            text = text.split('>', 1)[1]
    if text.count('</%s' % tag):
        text = text.split('</%s' % tag, 1)[0]

    text = text.strip().replace('\r\n', '\n')

    return text


# If you want PyTextile to automatically colorize
# your Python code, you need the htmlizer module
# from Twisted. (You can just grab this file from
# the distribution, it has no other dependencies.)
try:
    from twisted.python import htmlizer
    #import htmlizer # did they botch this up in the release? --cvh
    from StringIO import StringIO

    def _color(code):
        """Colorizer Python code.

        This function wraps a text string in a StringIO,
        and passes it to the htmlizer function from
        Twisted.
        """
        # Fix line continuations.
        code = preg_replace(r' \\\n', ' \\\\\n', code)
        
        code_in  = StringIO(code)
        code_out = StringIO()

        htmlizer.filter(code_in, code_out)

        # Remove <pre></pre> from input.
        code = _in_tag(code_out.getvalue(), 'pre')

        # Fix newlines.
        code = code.replace('<span class="py-src-newline">\n</span>', '<span class="py-src-newline"></span>\n')

        return code

except ImportError:
    htmlizer = None


# PyTextile can optionally validate the generated
# XHTML code using either mxTidy or uTidyLib.
try:
    # This is mxTidy.
    from mx.Tidy import Tidy
    
    def _tidy1(text):
        """mxTidy's XHTML validator.

        This function is a wrapper to mxTidy's validator.
        """
        nerrors, nwarnings, text, errortext = Tidy.tidy(text, output_xhtml=1, numeric_entities=1, wrap=0)
        return _in_tag(text, 'body')

    _tidy = _tidy1

except ImportError:
    try:
        # This is uTidyLib.
        import tidy

        def _tidy2(text):
            """uTidyLib's XHTML validator.

            This function is a wrapper to uTidyLib's validator.
            """
            text = tidy.parseString(text,  output_xhtml=1, add_xml_decl=0, indent=0, tidy_mark=0)
            return _in_tag(str(text), 'body')

        _tidy = _tidy2

    except ImportError:
        _tidy = None
    

# This is good for debugging.
def _debug(s, level=1):
    """Outputs debug information to sys.stderr.

    This function outputs debug information if DEBUGLEVEL is
    higher than a given treshold.
    """
    if DEBUGLEVEL >= level: print >> sys.stderr, s


#############################
# Useful regular expressions.
parameters = {
    # Horizontal alignment.
    'align':    r'''(?:(?:<>|[<>=])                 # Either '<>', '<', '>' or '='
                    (?![^\s]*(?:<>|[<>=])))         # Look-ahead to ensure it happens once
                 ''',

    # Horizontal padding.
    'padding':  r'''(?:[\(\)]+)                     # Any number of '(' and/or ')'
                 ''',

    # Class and/or id.
    'classid':  r'''(                               #
                        (?:\(\#[\w][\w\d\.:_-]*\))             # (#id)
                        |                           #
                        (?:\((?:[\w]+(?:\s[\w]+)*)  #
                            (?:\#[\w][\w\d\.:_-]*)?\))         # (class1 class2 ... classn#id) or (class1 class2 ... classn)
                    )                               #
                    (?![^\s]*(?:\([\w#]+\)))        # must happen once
                 ''',
           
    # Language.
    'lang':     r'''(?:\[[\w-]+\])                  # [lang]
                    (?![^\s]*(?:\[.*?\]))           # must happen once
                 ''',

    # Style.
    'style':    r'''(?:{[^\}]+})                    # {style}
                    (?![^\s]*(?:{.*?}))             # must happen once
                 ''',
}

res = {
    # Punctuation.
    'punct': r'''[\!"#\$%&'()\*\+,\-\./:;<=>\?@\[\\\]\^_`{\|}\~]''',
        
    # URL regular expression.
    'url':   r'''(?=[a-zA-Z0-9./#])                         # Must start correctly
                 (?:                                        # Match the leading part (proto://hostname, or just hostname)
                     (?:ftp|https?|telnet|nntp)             #     protocol
                     ://                                    #     ://
                     (?:                                    #     Optional 'username:password@'
                         \w+                                #         username
                         (?::\w+)?                          #         optional :password
                         @                                  #         @
                     )?                                     # 
                     [-\w]+(?:\.\w[-\w]*)+                  #     hostname (sub.example.com)
                 |                                          #
                     (?:mailto:)?                           #     Optional mailto:
                     [-\+\w]+                               #     username
                     \@                                     #     at
                     [-\w]+(?:\.\w[-\w]*)+                  #     hostname
                 |                                          #
                     (?:[a-z0-9](?:[-a-z0-9]*[a-z0-9])?\.)+ #     domain without protocol
                     (?:com\b                               #     TLD
                     |  edu\b                               #
                     |  biz\b                               #
                     |  gov\b                               #
                     |  in(?:t|fo)\b                        #     .int or .info
                     |  mil\b                               #
                     |  net\b                               #
                     |  org\b                               #
                     |  museum\b                            #
                     |  aero\b                              #
                     |  coop\b                              #
                     |  name\b                              #
                     |  pro\b                               #
                     |  [a-z][a-z]\b                        #     two-letter country codes
                     )                                      #
                 )?                                         #
                 (?::\d+)?                                  # Optional port number
                 (?:                                        # Rest of the URL, optional
                     /?                                     #     Start with '/'
                     [^.!,?;:"'<>()\[\]{}\s\x7F-\xFF]*      #     Can't start with these
                     (?:                                    #
                         [.!,?;:]+                          #     One or more of these
                         [^.!,?;:"'<>()\[\]{}\s\x7F-\xFF]+  #     Can't finish with these
                         #'"                                #     # or ' or "
                     )*                                     #
                 )?                                         #
              ''',


    # Block attributes.
    'battr': r'''(?P<parameters>                            # 
                     (?: %(align)s                          # alignment
                     |   %(classid)s                        # class and/or id
                     |   %(padding)s                        # padding tags
                     |   %(lang)s                           # [lang]
                     |   %(style)s                          # {style}
                     )+                                     #
                 )?                                         #
              ''' % parameters,

    # (Un)ordered list attributes.
    'olattr': r'''(?P<olparameters>                         # 
                      (?: %(align)s                         # alignment
                      | ((?:\(\#[\w]+\))                    # (#id)
                          |                                 #
                          (?:\((?:[\w]+(?:\s[\w]+)*)        #
                            (?:\#[\w]+)?\))                 # (class1 class2 ... classn#id) or (class1 class2 ... classn)
                      )                                     #
                      |   %(padding)s                       # padding tags
                      |   %(lang)s                          # [lang]
                      |   %(style)s                         # {style}
                      )+                                    #
                  )?                                        #
              ''' % parameters,

    # List item attributes.
    'liattr': r'''(?P<liparameters>                         # 
                      (?: %(align)s                         # alignment
                      |   %(classid)s                       # class and/or id
                      |   %(padding)s                       # padding tags
                      |   %(lang)s                          # [lang]
                      |   %(style)s                         # {style}
                      )+                                    #
                  )?                                        #
              ''' % parameters,

    # Qtag attributes.
    'qattr': r'''(?P<parameters>                            #
                     (?: %(classid)s                        # class and/or id
                     |   %(lang)s                           # [lang]
                     |   %(style)s                          # {style}
                     )+                                     #
                 )?                                         #
              ''' % parameters,

    # Link attributes.
    'lattr': r'''(?P<parameters>                            # Links attributes
                     (?: %(align)s                          # alignment
                     |   %(classid)s                        # class and/or id
                     |   %(lang)s                           # [lang]
                     |   %(style)s                          # {style}
                     )+                                     #
                 )?                                         #
              ''' % parameters,

    # Image attributes.
    'iattr': r'''(?P<parameters>                            #
                     (?:                                    #
                     (?: [<>]+                              # horizontal alignment tags
                         (?![^\s]*(?:[<>])))                #     (must happen once)
                     |                                      # 
                     (?: [\-\^~]+                           # vertical alignment tags
                         (?![^\s]*(?:[\-\^~])))             #     (must happen once)
                     | %(classid)s                          # class and/or id
                     | %(padding)s                          # padding tags
                     | %(style)s                            # {style}
                     )+                                     #
                 )?                                         #
              ''' % parameters,

    # Resize attributes.
    'resize': r'''(?:                                       #
                      (?:([\d]+%?)x([\d]+%?))               # 20x10
                      |                                     #
                      (?:                                   # or
                          (?:([\d]+)%?w\s([\d]+)%?h)        #     10h 20w
                          |                                 #     or
                          (?:([\d]+)%?h\s([\d]+)%?w)        #     20w 10h 
                      )                                     #
                  )?                                        #
               ''',

    # Table attributes.
    'tattr': r'''(?P<parameters>                            #
                     (?:                                    #
                     (?: [\^~]                              # vertical alignment
                         (?![^\s]*(?:[\^~])))               #     (must happen once)
                     |   %(align)s                          # alignment
                     |   %(lang)s                           # [lang]
                     |   %(style)s                          # {style}
                     |   %(classid)s                        # class and/or id
                     |   %(padding)s                        # padding
                     |   _                                  # is this a header row/cell?
                     |   \\\d+                              # colspan
                     |   /\d+                               # rowspan
                     )+                                     #
                 )?                                         #
              ''' % parameters,
}


def preg_replace(pattern, replacement, text):
    """Alternative re.sub that handles empty groups.

    This acts like re.sub, except it replaces empty groups with ''
    instead of raising an exception.
    """

    def replacement_func(matchobj):
        counter = 1
        rc = replacement
        _debug(matchobj.groups())
        for matchitem in matchobj.groups():
            if not matchitem:
                matchitem = ''

            rc = rc.replace(r'\%s' % counter, matchitem)
            counter += 1

        return rc
        
    p = re.compile(pattern)
    _debug(pattern)

    return p.sub(replacement_func, text)


def html_replace(pattern, replacement, text):
    """Replacement outside HTML tags.

    Does a preg_replace only outside HTML tags.
    """
    # If there is no html, do a simple search and replace.
    if not re.search(r'''<.*>''', text):
        return preg_replace(pattern, replacement, text)

    else:
        lines = []
        # Else split the text into an array at <>.
        for line in re.split('(<.*?>)', text):
            if not re.match('<.*?>', line):
                line = preg_replace(pattern, replacement, line)

            lines.append(line)

        return ''.join(lines)


# PyTextile can optionally sanitize the generated XHTML,
# which is good for weblog comments. This code is from
# Mark Pilgrim's feedparser.
class _BaseHTMLProcessor(sgmllib.SGMLParser):
    elements_no_end_tag = ['area', 'base', 'basefont', 'br', 'col', 'frame', 'hr',
      'img', 'input', 'isindex', 'link', 'meta', 'param']
    
    def __init__(self):
        sgmllib.SGMLParser.__init__(self)
    
    def reset(self):
        self.pieces = []
        sgmllib.SGMLParser.reset(self)

    def normalize_attrs(self, attrs):
        # utility method to be called by descendants
        attrs = [(k.lower(), sgmllib.charref.sub(lambda m: unichr(int(m.groups()[0])), v).strip()) for k, v in attrs]
        attrs = [(k, k in ('rel', 'type') and v.lower() or v) for k, v in attrs]
        return attrs
    
    def unknown_starttag(self, tag, attrs):
        # called for each start tag
        # attrs is a list of (attr, value) tuples
        # e.g. for <pre class="screen">, tag="pre", attrs=[("class", "screen")]
        strattrs = "".join([' %s="%s"' % (key, value) for key, value in attrs])
        if tag in self.elements_no_end_tag:
            self.pieces.append("<%(tag)s%(strattrs)s />" % locals())
        else:
            self.pieces.append("<%(tag)s%(strattrs)s>" % locals())
        
    def unknown_endtag(self, tag):
        # called for each end tag, e.g. for </pre>, tag will be "pre"
        # Reconstruct the original end tag.
        if tag not in self.elements_no_end_tag:
            self.pieces.append("</%(tag)s>" % locals())

    def handle_charref(self, ref):
        # called for each character reference, e.g. for "&#160;", ref will be "160"
        # Reconstruct the original character reference.
        self.pieces.append("&#%(ref)s;" % locals())

    def handle_entityref(self, ref):
        # called for each entity reference, e.g. for "&copy;", ref will be "copy"
        # Reconstruct the original entity reference.
        self.pieces.append("&%(ref)s;" % locals())

    def handle_data(self, text):
        # called for each block of plain text, i.e. outside of any tag and
        # not containing any character or entity references
        # Store the original text verbatim.
        self.pieces.append(text)

    def handle_comment(self, text):
        # called for each HTML comment, e.g. <!-- insert Javascript code here -->
        # Reconstruct the original comment.
        self.pieces.append("<!--%(text)s-->" % locals())

    def handle_pi(self, text):
        # called for each processing instruction, e.g. <?instruction>
        # Reconstruct original processing instruction.
        self.pieces.append("<?%(text)s>" % locals())

    def handle_decl(self, text):
        # called for the DOCTYPE, if present, e.g.
        # <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
        #     "http://www.w3.org/TR/html4/loose.dtd">
        # Reconstruct original DOCTYPE
        self.pieces.append("<!%(text)s>" % locals())

    def output(self):
        """Return processed HTML as a single string"""
        return "".join(self.pieces)


class _HTMLSanitizer(_BaseHTMLProcessor):
    acceptable_elements = ['a', 'abbr', 'acronym', 'address', 'area', 'b', 'big',
      'blockquote', 'br', 'button', 'caption', 'center', 'cite', 'code', 'col',
      'colgroup', 'dd', 'del', 'dfn', 'dir', 'div', 'dl', 'dt', 'em', 'fieldset',
      'font', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'input',
      'ins', 'kbd', 'label', 'legend', 'li', 'map', 'menu', 'ol', 'optgroup',
      'option', 'p', 'pre', 'q', 's', 'samp', 'select', 'small', 'span', 'strike',
      'strong', 'sub', 'sup', 'table', 'tbody', 'td', 'textarea', 'tfoot', 'th',
      'thead', 'tr', 'tt', 'u', 'ul', 'var']

    acceptable_attributes = ['abbr', 'accept', 'accept-charset', 'accesskey',
      'action', 'align', 'alt', 'axis', 'border', 'cellpadding', 'cellspacing',
      'char', 'charoff', 'charset', 'checked', 'cite', 'class', 'clear', 'cols',
      'colspan', 'color', 'compact', 'coords', 'datetime', 'dir', 'disabled',
      'enctype', 'for', 'frame', 'headers', 'height', 'href', 'hreflang', 'hspace',
      'id', 'ismap', 'label', 'lang', 'longdesc', 'maxlength', 'media', 'method',
      'multiple', 'name', 'nohref', 'noshade', 'nowrap', 'prompt', 'readonly',
      'rel', 'rev', 'rows', 'rowspan', 'rules', 'scope', 'selected', 'shape', 'size',
      'span', 'src', 'start', 'summary', 'tabindex', 'target', 'title', 'type',
      'usemap', 'valign', 'value', 'vspace', 'width']
    
    unacceptable_elements_with_end_tag = ['script', 'applet'] 
    
    # This if for MathML.
    mathml_elements = ['math', 'mi', 'mn', 'mo', 'mrow', 'msup']
    mathml_attributes = ['mode', 'xmlns']

    acceptable_elements = acceptable_elements + mathml_elements
    acceptable_attributes = acceptable_attributes + mathml_attributes
                  
    def reset(self):
        _BaseHTMLProcessor.reset(self)
        self.unacceptablestack = 0
        
    def unknown_starttag(self, tag, attrs):
        if not tag in self.acceptable_elements:
            if tag in self.unacceptable_elements_with_end_tag:
                self.unacceptablestack += 1
            return
        attrs = self.normalize_attrs(attrs)
        attrs = [(key, value) for key, value in attrs if key in self.acceptable_attributes]
        _BaseHTMLProcessor.unknown_starttag(self, tag, attrs)

    def unknown_endtag(self, tag):
        if not tag in self.acceptable_elements:
            if tag in self.unacceptable_elements_with_end_tag:
                self.unacceptablestack -= 1
            return
        _BaseHTMLProcessor.unknown_endtag(self, tag)

    def handle_pi(self, text):
        pass

    def handle_decl(self, text):
        pass

    def handle_data(self, text):
        if not self.unacceptablestack:
            _BaseHTMLProcessor.handle_data(self, text)


class Textiler:
    """Textile formatter.

    This is the base class for the PyTextile text processor.
    """
    def __init__(self, text=''):
        """Instantiate the class, passing the text to be formatted.
            
        Here we pre-process the text and collect all the link
        lookups for later.
        """
        self.text = text

        # Basic regular expressions.
        self.res = res

        # Smart searches.
        self.searches = {}
        self.searches['imdb']   = 'http://www.imdb.com/Find?for=%s'
        self.searches['google'] = 'http://www.google.com/search?q=%s'
        self.searches['python'] = 'http://www.python.org/doc/current/lib/module-%s.html'
        if amazon_associate_id:
            self.searches['isbn']   = ''.join(['http://', AMAZON, '/exec/obidos/ASIN/%s/', amazon_associate_id])
            self.searches['amazon'] = ''.join(['http://', AMAZON, '/exec/obidos/external-search?mode=blended&keyword=%s&tag=', amazon_associate_id])
        else:
            self.searches['isbn']   = ''.join(['http://', AMAZON, '/exec/obidos/ASIN/%s'])
            self.searches['amazon'] = ''.join(['http://', AMAZON, '/exec/obidos/external-search?mode=blended&keyword=%s'])

        # These are the blocks we know.
        self.signatures = [
                           # Paragraph.
                           (r'''^p                       # Paragraph signature
                                %(battr)s                # Paragraph attributes
                                (?P<dot>\.)              # .
                                (?P<extend>\.)?          # Extended paragraph denoted by a second dot
                                \s                       # whitespace
                                (?P<text>.*)             # text
                             ''' % self.res, self.paragraph),
   
                           # Pre-formatted text.
                           (r'''^pre                     # Pre signature
                                %(battr)s                # Pre attributes
                                (?P<dot>\.)              # .
                                (?P<extend>\.)?          # Extended pre denoted by a second dot
                                \s                       # whitespace
                                (?P<text>.*)             # text
                             ''' % self.res, self.pre),
   
                           # Block code.
                           (r'''^bc                      # Blockcode signature
                                %(battr)s                # Blockcode attributes
                                (?P<dot>\.)              # .
                                (?P<extend>\.)?          # Extended blockcode denoted by a second dot
                                \s                       # whitespace
                                (?P<text>.*)             # text
                             ''' % self.res, self.bc),
   
                           # Blockquote.
                           (r'''^bq                      # Blockquote signature
                                %(battr)s                # Blockquote attributes
                                (?P<dot>\.)              # .
                                (?P<extend>\.)?          # Extended blockquote denoted by a second dot
                                (:(?P<cite>              # Optional cite attribute
                                (                        #
                                    %(url)s              #     URL
                                |   "[\w]+(?:\s[\w]+)*"  #     "Name inside quotes"
                                ))                       #
                                )?                       #
                                \s                       # whitespace
                                (?P<text>.*)             # text
                             ''' % self.res, self.blockquote),
   
                           # Header.
                           (r'''^h                       # Header signature
                                (?P<header>\d)           # Header number
                                %(battr)s                # Header attributes
                                (?P<dot>\.)              # .
                                (?P<extend>\.)?          # Extended header denoted by a second dot
                                \s                       # whitespace
                                (?P<text>.*)             # text
                             ''' % self.res, self.header),
   
                           # Footnote.
                           (r'''^fn                      # Footnote signature
                                (?P<footnote>[\d]+)      # Footnote number
                                (?P<dot>\.)              # .
                                (?P<extend>\.)?          # Extended footnote denoted by a second dot
                                \s                       # whitespace
                                (?P<text>.*)             # text
                             ''', self.footnote),
   
                           # Definition list.
                           (r'''^dl                      # Definition list signature
                                %(battr)s                # Definition list attributes
                                (?P<dot>\.)              # .
                                (?P<extend>\.)?          # Extended definition list denoted by a second dot
                                \s                       # whitespace
                                (?P<text>.*)             # text
                             ''' % self.res, self.dl),
                           
                           # Ordered list (attributes to first <li>).
                           (r'''^%(olattr)s              # Ordered list attributes
                                \#                       # Ordered list signature
                                %(liattr)s               # List item attributes
                                (?P<dot>\.)?             # .
                                \s                       # whitespace
                                (?P<text>.*)             # text
                             ''' % self.res, self.ol),
   
                           # Unordered list (attributes to first <li>).
                           (r'''^%(olattr)s              # Unrdered list attributes
                                \*                       # Unordered list signature
                                %(liattr)s               # Unordered list attributes
                                (?P<dot>\.)?             # .
                                \s                       # whitespace
                                (?P<text>.*)             # text
                             ''' % self.res, self.ul),
   
                           # Escaped text.
                           (r'''^==?(?P<text>.*?)(==)?$  # Escaped text
                             ''', self.escape),
   
                           (r'''^(?P<text><.*)$          # XHTML tag
                             ''', self.escape),
   
                           # itex code.
                           (r'''^(?P<text>               # itex code
                                \\\[                     # starts with \[
                                .*?                      # complicated mathematical equations go here
                                \\\])                    # ends with \]
                             ''', self.itex),
   
                           # Tables.
                           (r'''^table                   # Table signature
                                %(tattr)s                # Table attributes
                                (?P<dot>\.)              # .
                                (?P<extend>\.)?          # Extended blockcode denoted by a second dot
                                \s                       # whitespace
                                (?P<text>.*)             # text
                             ''' % self.res, self.table),
                           
                           # Simple tables.
                           (r'''^(?P<text>
                                \|
                                .*)
                             ''', self.table),
   
                           # About.
                           (r'''^(?P<text>tell\sme\sabout\stextile\.)$''', self.about),
                          ]


    def preprocess(self):
        """Pre-processing of the text.

        Remove whitespace, fix carriage returns.
        """
        # Remove whitespace.
        self.text = self.text.strip()

        # Zap carriage returns.
        self.text = self.text.replace("\r\n", "\n")
        self.text = self.text.replace("\r", "\n")

        # Minor sanitizing.
        self.text = self.sanitize(self.text)


    def grab_links(self):
        """Grab link lookups.

        Check the text for link lookups, store them in a 
        dictionary, and clean them up.
        """
        # Grab links like this: '[id]example.com'
        links = {}
        p = re.compile(r'''(?:^|\n)\[([\w]+?)\](%(url)s)(?:$|\n)''' % self.res, re.VERBOSE)
        for key, link in p.findall(self.text):
            links[key] = link

        # And clear them from the text.
        self.text = p.sub('', self.text)

        return links


    def process(self, head_offset=HEAD_OFFSET, validate=VALIDATE, sanitize=SANITIZE, output=OUTPUT, encoding=ENCODING):
        """Process the text.

        Here we actually process the text, splitting the text in
        blocks and applying the corresponding function to each
        one of them.
        """
        # Basic global changes.
        self.preprocess()

        # Grab lookup links and clean them from the text.
        self._links = self.grab_links()

        # Offset for the headers.
        self.head_offset = head_offset

        # Process each block.
        self.blocks = self.split_text()

        text = []
        for [function, captures] in self.blocks:
            text.append(function(**captures))

        text = '\n\n'.join(text)

        # Add titles to footnotes.
        text = self.footnotes(text)

        # Convert to desired output.
        text = unicode(text, encoding)
        text = text.encode(output, 'xmlcharrefreplace')

        # Sanitize?
        if sanitize:
            p = _HTMLSanitizer()
            p.feed(text)
            text = p.output()

        # Validate output.
        if _tidy and validate:
            text = _tidy(text)

        return text


    def sanitize(self, text):
        """Fix single tags.

        Fix tags like <img />, <br /> and <hr />.

        ---
        h1. Sanitizing

        Textile can help you generate valid XHTML(eXtensible HyperText Markup Language).
        It will fix any single tags that are not properly closed, like
        @<img />@, @<br />@ and @<hr />@.

        If you have "mx.Tidy":http://www.egenix.com/files/python/mxTidy.html
        and/or "&micro;TidyLib":http://utidylib.sourceforge.net/ installed,
        it also can optionally validade the generated code with these wrappers
        to ensure 100% valid XHTML(eXtensible HyperText Markup Language).
        """
        # Fix single tags like <img /> and <br />.
        text = preg_replace(r'''<(img|br|hr)(.*?)(?:\s*/?\s*)?>''', r'''<\1\2 />''', text)

        # Remove ampersands.
        text = preg_replace(r'''&(?!#?[xX]?(?:[0-9a-fA-F]+|\w{1,8});)''', r'''&amp;''', text)

        return text


    def split_text(self):
        """Process the blocks from the text.

        Split the blocks according to the signatures, join extended
        blocks and associate each one of them with a function to
        process them.

        ---
        h1. Blocks

        Textile process your text by dividing it in blocks. Each block
        is identified by a signature and separated from other blocks by
        an empty line.

        All signatures should end with a period followed by a space. A
        header @<h1></h1>@ can be done this way:

        pre. h1. This is a header 1.

        Blocks may continue for multiple paragraphs of text. If you want
        a block signature to stay "active", use two periods after the
        signature instead of one. For example:

        pre.. bq.. This is paragraph one of a block quote.

        This is paragraph two of a block quote.

        =p. Now we're back to a regular paragraph.

        p. Becomes:
        
        pre.. <blockquote>
        <p>This is paragraph one of a block quote.</p>

        <p>This is paragraph two of a block quote.</p>
        </blockquote>

        <p>Now we&#8217;re back to a regular paragraph.</p>

        p. The blocks can be customised by adding parameters between the
        signature and the period. These include:

        dl. {style rule}:A CSS(Cascading Style Sheets) style rule.
        [ll]:A language identifier (for a "lang" attribute).
        (class) or (#id) or (class#id):For CSS(Cascading Style Sheets) class and id attributes.
        &gt;, &lt;, =, &lt;&gt;:Modifier characters for alignment. Right-justification, left-justification, centered, and full-justification. The paragraph will also receive the class names "right", "left", "center" and "justify", respectively.
        ( (one or more):Adds padding on the left. 1em per "(" character is applied. When combined with the align-left or align-right modifier, it makes the block float. 
        ) (one or more):Adds padding on the right. 1em per ")" character is applied. When combined with the align-left or align-right modifier, it makes the block float.

        Here's an overloaded example:

        pre. p(())>(class#id)[en]{color:red}. A simple paragraph.

        Becomes:

        pre. <p lang="en" style="color:red;padding-left:2em;padding-right:2em;float:right;" class="class right" id="id">A simple paragraph.</p>
        """
        # Clear signature.
        clear_sig = r'''^clear(?P<alignment>[<>])?\.$'''
        clear = None

        extending  = 0

        # We capture the \n's because they are important inside "pre..".
        blocks = re.split(r'''((\n){2,})''', self.text)
        output = []
        for block in blocks:
            block = block.strip()
            # Check for the clear signature.
            m = re.match(clear_sig, block)
            if m:
                clear = m.group('alignment')
                if clear:
                    clear = {'<': 'clear:left;', '>': 'clear:right;'}[clear]
                else:
                    clear = 'clear:both;'

            else:
                # Check each of the code signatures.
                for regexp, function in self.signatures:
                    p = re.compile(regexp, (re.VERBOSE | re.DOTALL))
                    m = p.match(block)
                    if m:
                        # Put everything in a dictionary.
                        captures = m.groupdict()

                        # If we are extending a block, we require a dot to
                        # break it, so we can start lines with '#' inside
                        # an extended <pre> without matching an ordered list.
                        if extending and not captures.get('dot', None):
                            output[-1][1]['text'] += block
                            break 
                        elif captures.has_key('dot'):
                            del captures['dot']
                            
                        # If a signature matches, we are not extending a block.
                        extending = 0

                        # Check if we should extend this block.
                        if captures.has_key('extend'):
                            extending = captures['extend']
                            del captures['extend']
                            
                        # Apply head_offset.
                        if captures.has_key('header'):
                            captures['header'] = int(captures['header']) + self.head_offset

                        # Apply clear.
                        if clear:
                            captures['clear'] = clear
                            clear = None

                        # Save the block to be processed later.
                        output.append([function, captures])

                        break

                else:
                    # Only add blocks with content and strip their
                    # heads & tails.. In turn, prepend them with two
                    # newlines. This makes bc output correct number
                    # of newlines. --cvh
                    if extending and block.rstrip():
                        # Append the text to the last block.
                        output[-1][1]['text'] += ('\n\n' + block)
                    elif block.strip():
                        output.append([self.paragraph, {'text': block}])
    
        return output


    def parse_params(self, parameters, clear=None, align_type='block'):
        """Parse the parameters from a block signature.

        This function parses the parameters from a block signature,
        splitting the information about class, id, language and
        style. The positioning (indentation and alignment) is parsed
        and stored in the style.

        A paragraph like:

            p>(class#id){color:red}[en]. Paragraph.

        or:
            
            p{color:red}[en](class#id)>. Paragraph.

        will have its parameters parsed to:

            output = {'lang' : 'en',
                      'class': 'class',
                      'id'   : 'id',
                      'style': 'color:red;text-align:right;'}

        Note that order is not important.
        """
        if not parameters:
            if clear:
                return {'style': clear}
            else:
                return {}

        output = {}
        
        # Match class from (class) or (class#id).
        m = re.search(r'''\((?P<class>[\w]+(\s[\w]+)*)(\#[\w][\w\d\.:_-]*)?\)''', parameters)
        if m: output['class'] = m.group('class')

        # Match id from (#id) or (class#id).
        m = re.search(r'''\([\w]*(\s[\w]+)*\#(?P<id>[\w][\w\d\.:_-]*)\)''', parameters)
        if m: output['id'] = m.group('id')

        # Match [language].
        m = re.search(r'''\[(?P<lang>[\w-]+)\]''', parameters)
        if m: output['lang'] = m.group('lang')

        # Match {style}.
        m = re.search(r'''{(?P<style>[^\}]+)}''', parameters)
        if m:
            output['style'] = m.group('style').replace('\n', '')

            # If necessary, apppend a semi-comma to the style.
            if not output['style'].endswith(';'):
                output['style'] += ';'

        # Clear the block?
        if clear:
            output['style'] = output.get('style', '') + clear

        # Remove classes, ids, langs and styles. This makes the 
        # regular expression for the positioning much easier.
        parameters = preg_replace(r'''\([\#\w\d\.:_\s-]+\)''', '', parameters)
        parameters = preg_replace(r'''\[[\w-]+\]''', '', parameters)
        parameters = preg_replace(r'''{[\w:;#%-]+}''', '', parameters)

        style = []
        
        # Count the left indentation.
        l_indent = parameters.count('(')
        if l_indent: style.append('padding-left:%dem;' % l_indent)

        # Count the right indentation.
        r_indent = parameters.count(')')
        if r_indent: style.append('padding-right:%dem;' % r_indent)

        # Add alignment.
        if align_type == 'image':
            align = [('<', 'float:left;', ' left'),
                     ('>', 'float:right;', ' right')]

            valign = [('^', 'vertical-align:text-top;', ' top'),
                      ('-', 'vertical-align:middle;', ' middle'),
                      ('~', 'vertical-align:text-bottom;', ' bottom')]

            # Images can have both a vertical and a horizontal alignment.
            for alignments in [align, valign]:
                for _align, _style, _class in alignments:
                    if parameters.count(_align):
                        style.append(_style)
                        
                        # Append a class name related to the alignment.
                        output['class'] = output.get('class', '') + _class
                        break

        elif align_type == 'table':
            align = [('<', 'left'),
                     ('>', 'right'),
                     ('=', 'center'),
                     ('<>', 'justify')]

            valign = [('^', 'top'),
                      ('~', 'bottom')]

            # Horizontal alignment.
            for _align, _style, in align:
                if parameters.count(_align):
                    output['align'] = _style
            
            # Vertical alignment.
            for _align, _style, in valign:
                if parameters.count(_align):
                    output['valign'] = _style

            # Colspan and rowspan.
            m = re.search(r'''\\(\d+)''', parameters)
            if m:
                #output['colspan'] = m.groups()
                output['colspan'] = int(m.groups()[0])

            m = re.search(r'''/(\d+)''', parameters)
            if m:
                output['rowspan'] = int(m.groups()[0])

        else:
            if l_indent or r_indent:
                alignments = [('<>', 'text-align:justify;', ' justify'),
                              ('=', 'text-align:center;', ' center'),
                              ('<', 'float:left;', ' left'),
                              ('>', 'float:right;', ' right')]
            else:
                alignments = [('<>', 'text-align:justify;', ' justify'),
                              ('=', 'text-align:center;', ' center'),
                              ('<', 'text-align:left;', ' left'),
                              ('>', 'text-align:right;', ' right')]

            for _align, _style, _class in alignments:
                if parameters.count(_align):
                    style.append(_style)

                    # Append a class name related to the alignment.
                    output['class'] = output.get('class', '') + _class
                    break

        # Join all the styles.
        output['style'] = output.get('style', '') + ''.join(style)

        # Remove excess whitespace.
        if output.has_key('class'):
            output['class'] = output['class'].strip()

        return output 
        

    def build_open_tag(self, tag, attributes={}, single=0):
        """Build the open tag with specified attributes.

        This function is used by all block builders to 
        generate the opening tags with the attributes of
        the block.
        """
        # Open tag.
        open_tag = ['<%s' % tag]
        for k,v in attributes.items():
            # The ALT attribute can be empty.
            if k == 'alt' or v: open_tag.append(' %s="%s"' % (k, v))

        if single:
            open_tag.append(' /')

        # Close tag.
        open_tag.append('>')

        return ''.join(open_tag)


    def paragraph(self, text, parameters=None, attributes=None, clear=None):
        """Process a paragraph.

        This function processes the paragraphs, enclosing the text in a 
        <p> tag and breaking lines with <br />. Paragraphs are formatted
        with all the inline rules.

        ---
        h1. Paragraph
        
        This is how you write a paragraph:

        pre. p. This is a paragraph, although a short one.
        
        Since the paragraph is the default block, you can safely omit its
        signature ([@p@]). Simply write:

        pre. This is a paragraph, although a short one.

        Text in a paragraph block is wrapped in @<p></p>@ tags, and
        newlines receive a <br /> tag. In both cases Textile will process
        the text to:

        pre. <p>This is a paragraph, although a short one.</p>

        Text in a paragraph block is processed with all the inline rules.
        """
        # Split the lines.
        lines = re.split('\n{2,}', text)
        
        # Get the attributes.
        attributes = attributes or self.parse_params(parameters, clear)

        output = []
        for line in lines:
            if line:
                # Clean the line.
                line = line.strip()
                 
                # Build the tag.
                open_tag = self.build_open_tag('p', attributes)
                close_tag = '</p>'

                # Pop the id because it must be unique.
                if attributes.has_key('id'): del attributes['id']

                # Break lines. 
                line = preg_replace(r'(<br />|\n)+', '<br />\n', line)

                # Remove <br /> from inside broken HTML tags.
                line = preg_replace(r'(<[^>]*)<br />\n(.*?>)', r'\1 \2', line)

                # Inline formatting.
                line = self.inline(line)

                output.append(open_tag + line + close_tag)

        return '\n\n'.join(output)


    def pre(self, text, parameters=None, clear=None):
        """Process pre-formatted text.

        This function processes pre-formatted text into a <pre> tag.
        No HTML is added for the lines, but @<@ and @>@ are translated into
        HTML entities.

        ---
        h1. Pre-formatted text

        Pre-formatted text can be specified using the @pre@ signature.
        Inside a "pre" block, whitespace is preserved and @<@ and @>@ are
        translated into HTML(HyperText Markup Language) entities
        automatically.

        Text in a "pre" block is _not processed_ with any inline rule.

        Here's a simple example:

        pre. pre. This text is pre-formatted.
        Nothing interesting happens inside here...
        
        Will become:

        pre. <pre>
        This text is pre-formatted.
        Nothing interesting happens inside here...
        </pre>
        """

        # Remove trailing whitespace.
        text = text.rstrip()

        # Get the attributes.
        attributes = self.parse_params(parameters, clear)

        # Build the tag.
        #open_tag = self.build_open_tag('pre', attributes) + '\n'
        open_tag = self.build_open_tag('pre', attributes)
        close_tag = '\n</pre>'

        # Replace < and >.
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')

        return open_tag + text + close_tag


    def bc(self, text, parameters=None, clear=None):
        """Process block code.

        This function processes block code into a <code> tag inside a
        <pre>. No HTML is added for the lines, but @<@ and @>@ are translated
        into HTML entities.

        ---
        h1. Block code

        A block code, specified by the @bc@ signature, is a block of
        pre-formatted text which also receives a @<code></code>@ tag. As
        with "pre", whitespace is preserved and @<@ and @>@ are translated
        into HTML(HyperText Markup Language) entities automatically.

        Text in a "bc" code is _not processed_ with the inline rules.
        
        If you have "Twisted":http://www.twistedmatrix.com/ installed,
        Textile can automatically colorize your Python code if you
        specify its language as "Python":
        
        pre. bc[python]. from twisted.python import htmlizer

        This will become:

        pre. <pre>
        <code lang="python">
        <span class="py-src-keyword">from</span> <span class="py-src-variable">twisted</span><span class="py-src-op">.</span><span class="py-src-variable">python</span> <span class="py-src-keyword">import</span> <span class="py-src-variable">htmlizer</span>
        </code>
        </pre>

        The colors can be specified in your CSS(Cascading Style Sheets)
        file. If you don't want to install Twisted, you can download just
        the @htmlizer@ module "independently":http://dealmeida.net/code/htmlizer.py.txt.
        """

        # Get the attributes.
        attributes = self.parse_params(parameters, clear)

        # XHTML <code> can't have the attribute lang.
        if attributes.has_key('lang'):
            lang = attributes['lang']
            del attributes['lang']
        else:
            lang = None

        # Build the tag.
        open_tag = '<pre>\n' + self.build_open_tag('code', attributes) + '\n'
        close_tag = '\n</code>\n</pre>'
        
        # Colorize Python code?
        if htmlizer and lang == 'python':
            text = _color(text)
            # colorizing adds extra newline... handle it --cvh
            close_tag = '</code>\n</pre>'
        else:
            # Replace < and >.
            text = text.replace('<', '&lt;')
            text = text.replace('>', '&gt;')

        return open_tag + text + close_tag


    def dl(self, text, parameters=None, clear=None):
        """Process definition list.

        This function process definition lists. The text inside
        the <dt> and <dd> tags is processed for inline formatting.

        ---
        h1. Definition list

        A definition list starts with the signature @dl@, and has
        its items separated by a @:@. Here's a simple example:

        pre. dl. name:Sir Lancelot of Camelot.
        quest:To seek the Holy Grail.
        color:Blue.

        Becomes:

        pre. <dl>
        <dt>name</dt>
        <dd>Sir Lancelot of Camelot.</dd>
        <dt>quest</dt>
        <dd>To seek the Holy Grail.</dd>
        <dt>color</dt>
        <dd>Blue.</dd>
        </dl>
        """
        # Get the attributes.
        attributes = self.parse_params(parameters, clear)

        # Build the tag.
        open_tag = self.build_open_tag('dl', attributes) + '\n'
        close_tag = '\n</dl>'

        lines = text.split('\n')
        output = []
        for line in lines:
            if line.count(':'):
                [dt, dd] = line.split(':', 1)
            else:
                dt,dd = line, ''

            if dt: output.append('<dt>%s</dt>\n<dd>%s</dd>' % (dt, dd))

        text = '\n'.join(output)

        text = self.inline(text)

        return open_tag + text + close_tag


    def blockquote(self, text, parameters=None, cite=None, clear=None):
        """Process block quote.

        The block quote is inserted into a <blockquote> tag, and
        processed as a paragraph. An optional cite attribute can
        be appended on the last line after two dashes (--), or
        after the period following ':' for compatibility with the
        Perl version.

        ---
        h1. Blockquote

        A blockquote is denoted by the signature @bq@. The text in this
        block will be enclosed in @<blockquote></blockquote>@ and @<p></p>@,
        receiving the same formatting as a paragraph. For example:

        pre. bq. This is a blockquote.

        Becomes:

        pre. <blockquote>
        <p>This is a blockquote.</p>
        </blockquote>

        You can optionally specify the @cite@ attribute of the blockquote,
        using the following syntax:

        pre. bq.:http://example.com Some text.

        pre. bq.:"John Doe" Some other text.

        Becomes:

        pre. <blockquote cite="http://example.com">
        <p>Some text.</p>
        </blockquote>

        pre. <blockquote cite="John Doe">
        <p>Some other text.</p>
        </blockquote>

        You can also specify the @cite@ using a pair of dashes on the
        last line of the blockquote:

        pre. bq. Some text.
        -- http://example.com
        """

        # Get the attributes.
        attributes = self.parse_params(parameters, clear)

        if cite:
            # Remove the quotes?
            cite = cite.strip('"')
            attributes['cite'] = cite
        else:
            # The citation should be on the last line.
            text = text.split('\n')
            if text[-1].startswith('-- '):
                attributes['cite'] = text.pop()[3:]    
        
            text = '\n'.join(text)

        # Build the tag.
        open_tag = self.build_open_tag('blockquote', attributes) + '\n'
        close_tag = '\n</blockquote>'

        # Process the paragraph, passing the attributes.
        # Does it make sense to pass the id, class, etc. to
        # the paragraph instead of applying it to the
        # blockquote tag?
        text = self.paragraph(text)
        
        return open_tag + text + close_tag


    def header(self, text, parameters=None, header=1, clear=None):
        """Process a header.

        The header number is captured by the regular 
        expression and lives in header. If head_offset is
        set, it is adjusted accordingly.

        ---
        h1. Header

        A header is produced by the signature @hn@, where @n@ goes
        from 1 to 6. You can adjust the relative output of the headers
        passing a @head_offset@ attribute when calling @textile()@.

        To make a header:

        pre. h1. This is a header.

        Becomes:

        pre. <h1>This is a header.</h1>
        """
        # Get the attributes.
        attributes = self.parse_params(parameters, clear)

        # Get the header number and limit it between 1 and 6.
        n = header
        n = min(n,6)
        n = max(n,1)

        # Build the tag.
        open_tag = self.build_open_tag('h%d' % n, attributes)
        close_tag = '</h%d>' % n

        text = self.inline(text)

        return open_tag + text + close_tag


    def footnote(self, text, parameters=None, footnote=1, clear=None):
        """Process a footnote.

        A footnote is formatted as a paragraph of class
        'footnote' and id 'fn%d', starting with the footnote
        number in a <sup> tag. Here we just build the
        attributes and pass them directly to self.paragraph().

        ---
        h1. Footnote

        A footnote is produced by the signature @fn@ followed by
        a number. Footnotes are paragraphs of a special CSS(Cascading Style Sheets)
        class. An example:

        pre. fn1. This is footnote number one.

        Will produce this:

        pre. <p class="footnote" id="fn1"><sup>1</sup> This is footnote number one.</p>

        This footnote can be referenced anywhere on the text by the
        following way:

        pre. This is a reference[1] to footnote number one.

        Which becomes:

        pre. <p>This is a reference<sup class="footnote"><a href="#fn1" title="This is footnote number one.">1</a></sup> to footnote number 1.</p>

        Note that the text from the footnote appears in the @title@ of the
        link pointing to it.
        """
        # Get the number.
        n = int(footnote)

        # Build the attributes to the paragraph.
        attributes = self.parse_params(parameters, clear)
        attributes['class'] = 'footnote'
        attributes['id']    = 'fn%d' % n

        # Build the paragraph text.
        text = ('<sup>%d</sup> ' % n) + text

        # And return the paragraph.
        return self.paragraph(text=text, attributes=attributes)


    def build_li(self, items, liattributes):
        """Build the list item.

        This function build the list item of an (un)ordered list. It
        works by peeking at the next list item, and searching for a
        multi-list. If a multi-list is found, it is processed and 
        appended inside the list item tags, as it should be.
        """
        lines = []
        while len(items):
            item = items.pop(0)

            # Clean the line.
            item = item.lstrip()
            item = item.replace('\n', '<br />\n')

            # Get list item attributes.
            p = re.compile(r'''^%(liattr)s\s''' % self.res, re.VERBOSE)
            m = p.match(item)
            if m:
                c = m.groupdict('')
                liparameters = c['liparameters']
                item = p.sub('', item)
            else:
                liparameters = ''

            liattributes = liattributes or self.parse_params(liparameters)
            
            # Build the item tag.
            open_tag_li = self.build_open_tag('li', liattributes) 

            # Reset the attributes, which should be applied
            # only to the first <li>.
            liattributes = {}

            # Build the closing tag.
            close_tag_li = '</li>'

            # Multi-list recursive routine.
            # Here we check the _next_ items for a multi-list. If we
            # find one, we extract all items of the multi-list and
            # process them recursively.
            if len(items):
                inlist = []

                # Grab all the items that start with # or *.
                n_item = items.pop(0)

                # Grab the <ol> parameters.
                p = re.compile(r'''^%(olattr)s''' % self.res, re.VERBOSE)
                m = p.match(n_item)
                if m:
                    c = m.groupdict('')
                    olparameters = c['olparameters']
                    tmp = p.sub('', n_item)
                else:
                    olparameters = ''

                # Check for an ordered list inside this one.
                if tmp.startswith('#'):
                    n_item = tmp
                    inlist.append(n_item)
                    while len(items):
                        # Peek into the next item.
                        n_item = items.pop(0)
                        if n_item.startswith('#'):
                            inlist.append(n_item)
                        else:
                            items.insert(0, n_item)
                            break
                        
                    inlist = self.ol('\n'.join(inlist), olparameters=olparameters)
                    item = item + '\n' + inlist + '\n'

                # Check for an unordered list inside this one.
                elif tmp.startswith('*'):
                    n_item = tmp
                    inlist.append(n_item)
                    while len(items):
                        # Peek into the next item.
                        n_item = items.pop(0)
                        if n_item.startswith('*'):
                            inlist.append(n_item)
                        else:
                            items.insert(0, n_item)
                            break

                    inlist = self.ul('\n'.join(inlist), olparameters=olparameters)
                    item = item + '\n' + inlist + '\n'

                # Otherwise we just put it back in the list.
                else:
                    items.insert(0, n_item)

            item = self.inline(item)

            item = open_tag_li + item + close_tag_li
            lines.append(item)

        return '\n'.join(lines)


    def ol(self, text, liparameters=None, olparameters=None, clear=None):
        """Build an ordered list.

        This function basically just sets the <ol></ol> with the
        right attributes, and then pass everything inside to 
        _build_li, which does the real tough recursive job.

        ---
        h1. Ordered lists

        Ordered lists can be constructed this way:

        pre. # Item number 1.
        # Item number 2.
        # Item number 3.

        And you get:

        pre. <ol>
        <li>Item number 1.</li>
        <li>Item number 2.</li>
        <li>Item number 3.</li>
        </ol>

        If you want a list to "break" an extended block, you should
        add a period after the hash. This is useful for writing 
        Python code:

        pre.. bc[python].. #!/usr/bin/env python

        # This is a comment, not an ordered list!
        # So this won't break the extended "bc".

        p. Lists can be nested:

        pre. # Item number 1.
        ## Item number 1a.
        ## Item number 1b.
        # Item number 2.
        ## Item number 2a.

        Textile will transform this to:

        pre. <ol>
        <li>Item number 1.
        <ol>
        <li>Item number 1a.</li>
        <li>Item number 1b.</li>
        </ol>
        </li>
        <li>Item number 2.
        <ol>
        <li>Item number 2a.</li>
        </ol>
        </li>
        </ol>

        You can also mix ordered and unordered lists:

        pre. * To write well you need:
        *# to read every day
        *# to write every day
        *# and X

        You'll get this:

        pre. <ul>
        <li>To write well you need:
        <ol>
        <li>to read every day</li>
        <li>to write every day</li>
        <li>and X</li>
        </ol>
        </li>
        </ul>

        To style a list, the parameters should go before the hash if you want
        to set the attributes on the @<ol>@ tag:

        pre. (class#id)# one
        # two
        # three

        If you want to customize the firsr @<li>@ tag, apply the parameters
        after the hash:

        pre. #(class#id) one
        # two
        # three
        """
        # Get the attributes.
        olattributes = self.parse_params(olparameters, clear)
        liattributes = self.parse_params(liparameters)

        # Remove list depth.
        if text.startswith('#'):
            text = text[1:]

        items = text.split('\n#')

        # Build the open tag.
        open_tag = self.build_open_tag('ol', olattributes) + '\n'

        close_tag = '\n</ol>'

        # Build the list items.
        text = self.build_li(items, liattributes)

        return open_tag + text + close_tag


    def ul(self, text, liparameters=None, olparameters=None, clear=None):
        """Build an unordered list.

        This function basically just sets the <ul></ul> with the
        right attributes, and then pass everything inside to 
        _build_li, which does the real tough recursive job.

        ---
        h1. Unordered lists

        Unordered lists behave exactly like the ordered lists, and are
        defined using a star:

        pre. * Python
        * Perl
        * PHP

        Becomes:

        pre. <ul>
        <li>Python</li>
        <li>Perl</li>
        <li><span class="caps">PHP</span></li>
        </ul>
        """
        # Get the attributes.
        olattributes = self.parse_params(olparameters, clear)
        liattributes = self.parse_params(liparameters)

        # Remove list depth.
        if text.startswith('*'):
            text = text[1:]

        items = text.split('\n*')

        # Build the open tag.
        open_tag = self.build_open_tag('ul', olattributes) + '\n'

        close_tag = '\n</ul>'

        # Build the list items.
        text = self.build_li(items, liattributes)

        return open_tag + text + close_tag
    

    def table(self, text, parameters=None, clear=None):
        """Build a table.

        To build a table we split the text in lines to get the
        rows, and split the rows between '|' to get the individual
        cells.

        ---
        h1. Tables

        Making a simple table is as easy as possible:

        pre. |a|b|c|
        |1|2|3|

        Will be processed into:

        pre. <table>
        <tr>
        <td>a</td>
        <td>b</td>
        <td>c</td>
        </tr>
        <tr>
        <td>1</td>
        <td>2</td>
        <td>3</td>
        </tr>
        </table>

        If you want to customize the @<table>@ tag, you must use the
        @table@ signature:

        pre. table(class#id)[en]. |a|b|c|
        |1|2|3|

        To customize a row, apply the modifier _before_ the first @|@:

        pre. table. (class)<>|a|b|c|
        |1|2|3|

        Individual cells can by customized by adding the parameters _after_
        the @|@, proceded by a period and a space:

        pre. |(#id). a|b|c|
        |1|2|3|

        The allowed modifiers are:

        dl. {style rule}:A CSS(Cascading Style Sheets) style rule. 
        (class) or (#id) or (class#id):A CSS(Cascading Style Sheets) class and/or id attribute. 
        ( (one or more):Adds 1em of padding to the left for each '(' character. 
        ) (one or more):Adds 1em of padding to the right for each ')' character. 
        &lt;:Aligns to the left (floats to left for tables if combined with the ')' modifier). 
        &gt;:Aligns to the right (floats to right for tables if combined with the '(' modifier). 
        =:Aligns to center (sets left, right margins to 'auto' for tables). 
        &lt;&gt;:For cells only. Justifies text. 
        ^:For rows and cells only. Aligns to the top. 
        ~ (tilde):For rows and cells only. Aligns to the bottom. 
        _ (underscore):Can be applied to a table row or cell to indicate a header row or cell. 
        \\2 or \\3 or \\4, etc.:Used within cells to indicate a colspan of 2, 3, 4, etc. columns. When you see "\\", think "push forward". 
        /2 or /3 or /4, etc.:Used within cells to indicate a rowspan of 2, 3, 4, etc. rows. When you see "/", think "push downward". 
        
        When a cell is identified as a header cell and an alignment is
        specified, that becomes the default alignment for cells below it.
        You can always override this behavior by specifying an alignment
        for one of the lower cells.
        """
        attributes = self.parse_params(parameters, clear, align_type='table')
        #attributes['cellspacing'] = '0'

        # Build the <table>.
        open_tag = self.build_open_tag('table', attributes) + '\n'
        close_tag = '</table>'

        output = []
        default_align = {}
        rows = re.split(r'''\n+''', text)
        for row in rows:
            # Get the columns.
            columns = row.split('|')

            # Build the <tr>.
            parameters = columns.pop(0)

            rowattr = self.parse_params(parameters, align_type='table')
            open_tr = self.build_open_tag('tr', rowattr) + '\n'
            output.append(open_tr)

            # Does the row define headers?
            if parameters.count('_'):
                td_tag = 'th'
            else:
                td_tag = 'td'
                
            col = 0
            for cell in columns[:-1]:
                p = re.compile(r'''(?:%(tattr)s\.\s)?(?P<text>.*)''' % self.res, re.VERBOSE)
                m = p.match(cell)
                if m:
                    c = m.groupdict('')
                    cellattr = self.parse_params(c['parameters'], align_type='table')

                    # Get the width of this cell.
                    width = cellattr.get('colspan', 1)

                    # Is this a header?
                    if c['parameters'].count('_'):
                        td_tag = 'th'

                    # If it is a header, let's set the default alignment.
                    if td_tag == 'th':
                        # Set the default aligment for all cells below this one.
                        # This is a little tricky because this header can have
                        # a colspan set.
                        for i in range(col, col+width):
                            default_align[i] = cellattr.get('align', None)

                    else:
                        # Apply the default align, if any.
                        cellattr['align'] = cellattr.get('align', default_align.get(col, None))

                    open_td = self.build_open_tag(td_tag, cellattr)
                    close_td = '</%s>\n' % td_tag

                    #output.append(open_td + c['text'].strip() + close_td)
                    output.append(open_td + self.inline(c['text'].strip()) + close_td)

                col += width

            output.append('</tr>\n')

        text = open_tag + ''.join(output) + close_tag

        return text


    def escape(self, text):
        """Do nothing.

        This is used to match escaped text. Nothing to see here!

        ---
        h1. Escaping

        If you don't want Textile processing a block, you can simply
        enclose it inside @==@:

        pre. p. Regular paragraph

        pre. ==
        Escaped portion -- will not be formatted
        by Textile at all
        ==

        pre. p. Back to normal.

        This can also be used inline, disabling the formatting temporarily:

        pre. p. This is ==*a test*== of escaping.
        """
        return text


    def itex(self, text):
        """Convert itex to MathML.

        If the itex2mml binary is set, we use it to convert the
        itex to MathML. Otherwise, the text is unprocessed and 
        return as is.

        ---
        h1. itex

        Textile can automatically convert itex code to MathML(Mathematical Markup Language)
        for you, if you have the itex2MML binary (you can download it
        from the "Movable Type plugin":http://golem.ph.utexas.edu/~distler/blog/files/itexToMML.tar.gz).

        Block equations should be enclosed inbetween @\[@ and @\]@:

        pre. \[ e^{i\pi} + 1 = 0 \]

        Will be translated to:

        pre. <math xmlns='http://www.w3.org/1998/Math/MathML' mode='display'>
        <msup><mi>e</mi> <mrow><mi>i</mi>
        <mi>&amp;pi;</mi></mrow></msup>
        <mo>+</mo><mn>1</mn><mo>=</mo><mn>0</mn>
        </math>

        Equations can also be displayed inline:

        pre. Euler's formula, $e^{i\pi}+1=0$, ...

        (Note that if you want to display MathML(Mathematical Markup Language)
        your content must be served as @application/xhtml+xml@, which is not
        accepted by all browsers.)
        """
        if itex2mml:
            try:
                text = os.popen("echo '%s' | %s" % (text, itex2mml)).read()
            except:
                pass

        return text


    def about(self, text=None):
        """Show PyTextile's functionalities.

        An introduction to PyTextile. Can be called when running the
        main script or if you write the following line:

            'tell me about textile.'

        But keep it a secret!
        """

        about = []
        about.append(textile('h1. This is Textile', head_offset=self.head_offset))
        about.append(textile(__doc__.split('---', 1)[1], head_offset=self.head_offset))

        functions = [(self.split_text, 1),
                     (self.paragraph,  2),
                     (self.pre,        2),
                     (self.bc,         2),
                     (self.blockquote, 2),
                     (self.dl,         2),
                     (self.header,     2),
                     (self.footnote,   2),
                     (self.escape,     2),
                     (self.itex,       2),
                     (self.ol,         2),
                     (self.ul,         2),
                     (self.table,      2),
                     (self.inline,     1),
                     (self.qtags,      2),
                     (self.glyphs,     2),
                     (self.macros,     2),
                     (self.acronym,    2),
                     (self.images,     1),
                     (self.links,      1),
                     (self.sanitize,   1),
                    ]

        for function, offset in functions:
            doc = function.__doc__.split('---', 1)[1]
            doc = doc.split('\n')
            lines = []
            for line in doc:
                line = line.strip()
                lines.append(line)
                
            doc = '\n'.join(lines)
            about.append(textile(doc, head_offset=self.head_offset+offset))

        about = '\n'.join(about)
        about = about.replace('<br />', '')

        return about


    def acronym(self, text):
        """Process acronyms.

        Acronyms can have letters in upper and lower caps, or even numbers,
        provided that the numbers and upper caps are the same in the
        abbreviation and in the description. For example:

            XHTML(eXtensible HyperText Markup Language)
            OPeNDAP(Open source Project for a Network Data Access Protocol)
            L94(Levitus 94)

        are all valid acronyms.

        ---
        h1. Acronyms

        You can define acronyms in your text the following way:

        pre. This is XHTML(eXtensible HyperText Markup Language).

        The resulting code is:

        pre. <p><acronym title="eXtensible HyperText Markup Language"><span class="caps">XHTML</span></acronym></p>

        Acronyms can have letters in upper and lower caps, or even numbers,
        provided that the numbers and upper caps are the same in the
        abbreviation and in the description. For example:

        pre. XHTML(eXtensible HyperText Markup Language)
        OPeNDAP(Open source Project for a Network Data Access Protocol)
        L94(Levitus 94)

        are all valid acronyms.
        """
        # Find the acronyms.
        acronyms = r'''(?P<acronym>[\w]+)\((?P<definition>[^\(\)]+?)\)'''

        # Check all acronyms.
        for acronym, definition in re.findall(acronyms, text):
            caps_acronym = ''.join(re.findall('[A-Z\d]+', acronym))
            caps_definition = ''.join(re.findall('[A-Z\d]+', definition))
            if caps_acronym and caps_acronym == caps_definition:
                text = text.replace('%s(%s)' % (acronym, definition), '<acronym title="%s">%s</acronym>' % (definition, acronym))
        
        text = html_replace(r'''(^|\s)([A-Z]{3,})\b(?!\()''', r'''\1<span class="caps">\2</span>''', text)

        return text


    def footnotes(self, text):
        """Add titles to footnotes references.

        This function searches for footnotes references like this [1], and 
        adds a title to the link containing the first paragraph of the
        footnote.
        """
        # Search for footnotes.
        p = re.compile(r'''<p class="footnote" id="fn(?P<n>\d+)"><sup>(?P=n)</sup>(?P<note>.*)</p>''')
        for m in p.finditer(text):
            n = m.group('n')
            note = m.group('note').strip()

            # Strip HTML from note.
            note = re.sub('<.*?>', '', note)

            # Add the title.
            text = text.replace('<a href="#fn%s">' % n, '<a href="#fn%s" title="%s">' % (n, note))

        return text


    def macros(self, m):
        """Quick macros.

        This function replaces macros inside brackets using a built-in
        dictionary, and also unicode names if the key doesn't exist.

        ---
        h1. Macros

        Textile has support for character macros, which should be enclosed
        in curly braces. A few useful ones are:

        pre. {C=} or {=C}: euro sign
        {+-} or {-+}: plus-minus sign
        {L-} or {-L}: pound sign.

        You can also make accented characters:

        pre. Expos{e'}

        Becomes:

        pre. <p>Expos&amp;#233;</p>

        You can also specify Unicode names like:

        pre. {umbrella}
        {white smiling face}
        """
        entity = m.group(1)

        macros = {'c|': '&#162;',       # cent sign
                  '|c': '&#162;',       # cent sign
                  'L-': '&#163;',       # pound sign
                  '-L': '&#163;',       # pound sign
                  'Y=': '&#165;',       # yen sign
                  '=Y': '&#165;',       # yen sign
                  '(c)': '&#169;',      # copyright sign
                  '<<': '&#171;',       # left-pointing double angle quotation
                  '(r)': '&#174;',      # registered sign
                  '+_': '&#177;',       # plus-minus sign
                  '_+': '&#177;',       # plus-minus sign
                  '>>': '&#187;',       # right-pointing double angle quotation
                  '1/4': '&#188;',      # vulgar fraction one quarter
                  '1/2': '&#189;',      # vulgar fraction one half
                  '3/4': '&#190;',      # vulgar fraction three quarters
                  'A`': '&#192;',       # latin capital letter a with grave
                  '`A': '&#192;',       # latin capital letter a with grave
                  'A\'': '&#193;',      # latin capital letter a with acute
                  '\'A': '&#193;',      # latin capital letter a with acute
                  'A^': '&#194;',       # latin capital letter a with circumflex
                  '^A': '&#194;',       # latin capital letter a with circumflex
                  'A~': '&#195;',       # latin capital letter a with tilde
                  '~A': '&#195;',       # latin capital letter a with tilde
                  'A"': '&#196;',       # latin capital letter a with diaeresis
                  '"A': '&#196;',       # latin capital letter a with diaeresis
                  'Ao': '&#197;',       # latin capital letter a with ring above
                  'oA': '&#197;',       # latin capital letter a with ring above
                  'AE': '&#198;',       # latin capital letter ae
                  'C,': '&#199;',       # latin capital letter c with cedilla
                  ',C': '&#199;',       # latin capital letter c with cedilla
                  'E`': '&#200;',       # latin capital letter e with grave
                  '`E': '&#200;',       # latin capital letter e with grave
                  'E\'': '&#201;',      # latin capital letter e with acute
                  '\'E': '&#201;',      # latin capital letter e with acute
                  'E^': '&#202;',       # latin capital letter e with circumflex
                  '^E': '&#202;',       # latin capital letter e with circumflex
                  'E"': '&#203;',       # latin capital letter e with diaeresis
                  '"E': '&#203;',       # latin capital letter e with diaeresis
                  'I`': '&#204;',       # latin capital letter i with grave
                  '`I': '&#204;',       # latin capital letter i with grave
                  'I\'': '&#205;',      # latin capital letter i with acute
                  '\'I': '&#205;',      # latin capital letter i with acute
                  'I^': '&#206;',       # latin capital letter i with circumflex
                  '^I': '&#206;',       # latin capital letter i with circumflex
                  'I"': '&#207;',       # latin capital letter i with diaeresis
                  '"I': '&#207;',       # latin capital letter i with diaeresis
                  'D-': '&#208;',       # latin capital letter eth
                  '-D': '&#208;',       # latin capital letter eth
                  'N~': '&#209;',       # latin capital letter n with tilde
                  '~N': '&#209;',       # latin capital letter n with tilde
                  'O`': '&#210;',       # latin capital letter o with grave
                  '`O': '&#210;',       # latin capital letter o with grave
                  'O\'': '&#211;',      # latin capital letter o with acute
                  '\'O': '&#211;',      # latin capital letter o with acute
                  'O^': '&#212;',       # latin capital letter o with circumflex
                  '^O': '&#212;',       # latin capital letter o with circumflex
                  'O~': '&#213;',       # latin capital letter o with tilde
                  '~O': '&#213;',       # latin capital letter o with tilde
                  'O"': '&#214;',       # latin capital letter o with diaeresis
                  '"O': '&#214;',       # latin capital letter o with diaeresis
                  'O/': '&#216;',       # latin capital letter o with stroke
                  '/O': '&#216;',       # latin capital letter o with stroke
                  'U`':  '&#217;',      # latin capital letter u with grave
                  '`U':  '&#217;',      # latin capital letter u with grave
                  'U\'': '&#218;',      # latin capital letter u with acute
                  '\'U': '&#218;',      # latin capital letter u with acute
                  'U^': '&#219;',       # latin capital letter u with circumflex
                  '^U': '&#219;',       # latin capital letter u with circumflex
                  'U"': '&#220;',       # latin capital letter u with diaeresis
                  '"U': '&#220;',       # latin capital letter u with diaeresis
                  'Y\'': '&#221;',      # latin capital letter y with acute
                  '\'Y': '&#221;',      # latin capital letter y with acute
                  'a`': '&#224;',       # latin small letter a with grave
                  '`a': '&#224;',       # latin small letter a with grave
                  'a\'': '&#225;',      # latin small letter a with acute
                  '\'a': '&#225;',      # latin small letter a with acute
                  'a^': '&#226;',       # latin small letter a with circumflex
                  '^a': '&#226;',       # latin small letter a with circumflex
                  'a~': '&#227;',       # latin small letter a with tilde
                  '~a': '&#227;',       # latin small letter a with tilde
                  'a"': '&#228;',       # latin small letter a with diaeresis
                  '"a': '&#228;',       # latin small letter a with diaeresis
                  'ao': '&#229;',       # latin small letter a with ring above
                  'oa': '&#229;',       # latin small letter a with ring above
                  'ae': '&#230;',       # latin small letter ae
                  'c,': '&#231;',       # latin small letter c with cedilla
                  ',c': '&#231;',       # latin small letter c with cedilla
                  'e`': '&#232;',       # latin small letter e with grave
                  '`e': '&#232;',       # latin small letter e with grave
                  'e\'': '&#233;',      # latin small letter e with acute
                  '\'e': '&#233;',      # latin small letter e with acute
                  'e^': '&#234;',       # latin small letter e with circumflex
                  '^e': '&#234;',       # latin small letter e with circumflex
                  'e"': '&#235;',       # latin small letter e with diaeresis
                  '"e': '&#235;',       # latin small letter e with diaeresis
                  'i`': '&#236;',       # latin small letter i with grave
                  '`i': '&#236;',       # latin small letter i with grave
                  'i\'': '&#237;',      # latin small letter i with acute
                  '\'i': '&#237;',      # latin small letter i with acute
                  'i^': '&#238;',       # latin small letter i with circumflex
                  '^i': '&#238;',       # latin small letter i with circumflex
                  'i"': '&#239;',       # latin small letter i with diaeresis
                  '"i': '&#239;',       # latin small letter i with diaeresis
                  'n~': '&#241;',       # latin small letter n with tilde
                  '~n': '&#241;',       # latin small letter n with tilde
                  'o`': '&#242;',       # latin small letter o with grave
                  '`o': '&#242;',       # latin small letter o with grave
                  'o\'': '&#243;',      # latin small letter o with acute
                  '\'o': '&#243;',      # latin small letter o with acute
                  'o^': '&#244;',       # latin small letter o with circumflex
                  '^o': '&#244;',       # latin small letter o with circumflex
                  'o~': '&#245;',       # latin small letter o with tilde
                  '~o': '&#245;',       # latin small letter o with tilde
                  'o"': '&#246;',       # latin small letter o with diaeresis
                  '"o': '&#246;',       # latin small letter o with diaeresis
                  ':-': '&#247;',       # division sign
                  '-:': '&#247;',       # division sign
                  'o/': '&#248;',       # latin small letter o with stroke
                  '/o': '&#248;',       # latin small letter o with stroke
                  'u`': '&#249;',       # latin small letter u with grave
                  '`u': '&#249;',       # latin small letter u with grave
                  'u\'': '&#250;',      # latin small letter u with acute
                  '\'u': '&#250;',      # latin small letter u with acute
                  'u^': '&#251;',       # latin small letter u with circumflex
                  '^u': '&#251;',       # latin small letter u with circumflex
                  'u"': '&#252;',       # latin small letter u with diaeresis
                  '"u': '&#252;',       # latin small letter u with diaeresis
                  'y\'': '&#253;',      # latin small letter y with acute
                  '\'y': '&#253;',      # latin small letter y with acute
                  'y"': '&#255',        # latin small letter y with diaeresis
                  '"y': '&#255',        # latin small letter y with diaeresis
                  'OE': '&#338;',       # latin capital ligature oe
                  'oe': '&#339;',       # latin small ligature oe
                  '*': '&#8226;',       # bullet
                  'Fr': '&#8355;',      # french franc sign
                  'L=': '&#8356;',      # lira sign
                  '=L': '&#8356;',      # lira sign
                  'Rs': '&#8360;',      # rupee sign
                  'C=': '&#8364;',      # euro sign
                  '=C': '&#8364;',      # euro sign
                  'tm': '&#8482;',      # trade mark sign
                  '<-': '&#8592;',      # leftwards arrow
                  '->': '&#8594;',      # rightwards arrow
                  '<=': '&#8656;',      # leftwards double arrow
                  '=>': '&#8658;',      # rightwards double arrow
                  '=/': '&#8800;',      # not equal to
                  '/=': '&#8800;',      # not equal to
                  '<_': '&#8804;',      # less-than or equal to
                  '_<': '&#8804;',      # less-than or equal to
                  '>_': '&#8805;',      # greater-than or equal to
                  '_>': '&#8805;',      # greater-than or equal to
                  ':(': '&#9785;',      # white frowning face
                  ':)': '&#9786;',      # white smiling face
                  'spade': '&#9824;',   # black spade suit
                  'club': '&#9827;',    # black club suit
                  'heart': '&#9829;',   # black heart suit
                  'diamond': '&#9830;', # black diamond suit
                 }

        try:
            # Try the key.
            entity = macros[entity]
        except KeyError:
            try:
                # Try a unicode entity.
                entity = unicodedata.lookup(entity)
                entity = entity.encode('ascii', 'xmlcharrefreplace')
            except:
                # Return the unmodified entity.
                entity = '{%s}' % entity

        return entity


    def glyphs(self, text):
        """Glyph formatting.

        This function replaces quotations marks, dashes and a few other
        symbol for numerical entities. The em/en dashes use definitions
        comes from http://alistapart.com/articles/emen/.

        ---
        h1. Glyphs

        Textile replaces some of the characters in your text with their
        equivalent numerical entities. These include:

        * Replace single and double primes used as quotation marks with HTML(HyperText Markup Language) entities for opening and closing quotation marks in readable text, while leaving untouched the primes required within HTML(HyperText Markup Language) tags.
        * Replace double hyphens (==--==) with an em-dash (&#8212;) entity.
        * Replace triple hyphens (==---==) with two em-dash (&#8212;&#8212;) entities.
        * Replace single hyphens surrounded by spaces with an en-dash (&#8211;) entity.
        * Replace triplets of periods (==...==) with an ellipsis (&#8230;) entity.
        * Convert many nonstandard characters to browser-safe entities corresponding to keyboard input.
        * Convert ==(TM)==, ==(R)==, and  ==(C)== to &#8482;, &#174;, and &#169;.
        * Convert the letter x to a dimension sign: 2==x==4 to 2x4 and 8 ==x== 10 to 8x10.
        """
        glyphs = [(r'''"(?<!\w)\b''', r'''&#8220;'''),                              # double quotes
                  (r'''"''', r'''&#8221;'''),                                       # double quotes
                  (r"""\b'""", r'''&#8217;'''),                                     # single quotes
                  (r"""'(?<!\w)\b""", r'''&#8216;'''),                              # single quotes
                  (r"""'""", r'''&#8217;'''),                                       # single single quote
                  (r'''(\b|^)( )?\.{3}''', r'''\1&#8230;'''),                       # ellipsis
                  (r'''\b---\b''', r'''&#8212;&#8212;'''),                          # double em dash
                  (r'''\s?--\s?''', r'''&#8212;'''),                                # em dash
                  (r'''(\d+)-(\d+)''', r'''\1&#8211;\2'''),                         # en dash (1954-1999)
                  (r'''(\d+)-(\W)''', r'''\1&#8212;\2'''),                          # em dash (1954--)
                  (r'''\s-\s''', r''' &#8211; '''),                                 # en dash
                  (r'''(\d+) ?x ?(\d+)''', r'''\1&#215;\2'''),                      # dimension sign
                  (r'''\b ?(\((tm|TM)\))''', r'''&#8482;'''),                       # trademark
                  (r'''\b ?(\([rR]\))''', r'''&#174;'''),                           # registered
                  (r'''\b ?(\([cC]\))''', r'''&#169;'''),                           # copyright
                  (r'''([^\s])\[(\d+)\]''',                                         #
                       r'''\1<sup class="footnote"><a href="#fn\2">\2</a></sup>'''),# footnote
                  ]

        # Apply macros.
        text = re.sub(r'''{([^}]+)}''', self.macros, text)

        # LaTeX style quotes.
        text = text.replace('\x60\x60', '&#8220;')
        text = text.replace('\xb4\xb4', '&#8221;')

        # Linkify URL and emails.
        url = r'''(?=[a-zA-Z0-9./#])                          # Must start correctly
                  ((?:                                        # Match the leading part (proto://hostname, or just hostname)
                      (?:ftp|https?|telnet|nntp)              #     protocol
                      ://                                     #     ://
                      (?:                                     #     Optional 'username:password@'
                          \w+                                 #         username
                          (?::\w+)?                           #         optional :password
                          @                                   #         @
                      )?                                      # 
                      [-\w]+(?:\.\w[-\w]*)+                   #     hostname (sub.example.com)
                  )                                           #
                  (?::\d+)?                                   # Optional port number
                  (?:                                         # Rest of the URL, optional
                      /?                                      #     Start with '/'
                      [^.!,?;:"'<>()\[\]{}\s\x7F-\xFF]*       #     Can't start with these
                      (?:                                     #
                          [.!,?;:]+                           #     One or more of these
                          [^.!,?;:"'<>()\[\]{}\s\x7F-\xFF]+   #     Can't finish with these
                          #'"                                 #     # or ' or "
                      )*                                      #
                  )?)                                         #
               '''

        email = r'''(?:mailto:)?            # Optional mailto:
                    ([-\+\w]+               # username
                    \@                      # at
                    [-\w]+(?:\.\w[-\w]*)+)  # hostname
                 '''

        # If there is no html, do a simple search and replace.
        if not re.search(r'''<.*>''', text):
            for glyph_search, glyph_replace in glyphs:
                text = preg_replace(glyph_search, glyph_replace, text)

            # Linkify.
            text = re.sub(re.compile(url, re.VERBOSE), r'''<a href="\1">\1</a>''', text)
            text = re.sub(re.compile(email, re.VERBOSE), r'''<a href="mailto:\1">\1</a>''', text)

        else:
            lines = []
            # Else split the text into an array at <>.
            for line in re.split('(<.*?>)', text):
                if not re.match('<.*?>', line):
                    for glyph_search, glyph_replace in glyphs:
                        line = preg_replace(glyph_search, glyph_replace, line)

                    # Linkify.
                    line = re.sub(re.compile(url, re.VERBOSE), r'''<a href="\1">\1</a>''', line)
                    line = re.sub(re.compile(email, re.VERBOSE), r'''<a href="mailto:\1">\1</a>''', line)

                lines.append(line)

            text = ''.join(lines)

        return text


    def qtags(self, text):
        """Quick tags formatting.

        This function does the inline formatting of text, like
        bold, italic, strong and also itex code.

        ---
        h1. Quick tags

        Quick tags allow you to format your text, making it bold, 
        emphasized or small, for example. The quick tags operators
        include:

        dl. ==*strong*==:Translates into @<strong>strong</strong>@.
        ==_emphasis_==:Translates into @<em>emphasis</em>@. 
        ==**bold**==:Translates into @<b>bold</b>@. 
        ==__italics__==:Translates into @<i>italics</i>@. 
        ==++bigger++==:Translates into @<big>bigger</big>@. 
        ==--smaller--==:Translates into: @<small>smaller</small>@. 
        ==-deleted text-==:Translates into @<del>deleted text</del>@. 
        ==+inserted text+==:Translates into @<ins>inserted text</ins>@. 
        ==^superscript^==:Translates into @<sup>superscript</sup>@. 
        ==~subscript~==:Translates into @<sub>subscript</sub>@. 
        ==%span%==:Translates into @<span>span</span>@. 
        ==@code@==:Translates into @<code>code</code>@. 
        
        Note that within a "==@==...==@==" section, @<@ and @>@ are
        translated into HTML entities automatically. 

        Inline formatting operators accept the following modifiers:

        dl. {style rule}:A CSS(Cascading Style Sheets) style rule. 
        [ll]:A language identifier (for a "lang" attribute). 
        (class) or (#id) or (class#id):For CSS(Cascading Style Sheets) class and id attributes. 
        """
        # itex2mml.
        text = re.sub('\$(.*?)\$', lambda m: self.itex(m.group()), text)

        # Add span tags to upper-case words which don't have a description.
        #text = preg_replace(r'''(^|\s)([A-Z]{3,})\b(?!\()''', r'''\1<span class="caps">\2</span>''', text)
        
        # Quick tags.
        qtags = [('**', 'b',      {'qf': '(?<!\*)\*\*(?!\*)', 'cls': '\*'}),
                 ('__', 'i',      {'qf': '(?<!_)__(?!_)', 'cls': '_'}),
                 ('??', 'cite',   {'qf': '\?\?(?!\?)', 'cls': '\?'}),
                 ('-',  'del',    {'qf': '(?<!\-)\-(?!\-)', 'cls': '-'}),
                 ('+',  'ins',    {'qf': '(?<!\+)\+(?!\+)', 'cls': '\+'}),
                 ('*',  'strong', {'qf': '(?<!\*)\*(?!\*)', 'cls': '\*'}),
                 ('_',  'em',     {'qf': '(?<!_)_(?!_)', 'cls': '_'}),
                 ('++', 'big',    {'qf': '(?<!\+)\+\+(?!\+)', 'cls': '\+\+'}),
                 ('--', 'small',  {'qf': '(?<!\-)\-\-(?!\-)', 'cls': '\-\-'}),
                 ('~',  'sub',    {'qf': '(?<!\~)\~(?!(\\\/~))', 'cls': '\~'}),
                 ('@',  'code',   {'qf': '(?<!@)@(?!@)', 'cls': '@'}),
                 ('%',  'span',   {'qf': '(?<!%)%(?!%)', 'cls': '%'}),
                ]

        # Superscript.
        text = re.sub(r'''(?<!\^)\^(?!\^)(.+?)(?<!\^)\^(?!\^)''', r'''<sup>\1</sup>''', text)

        # This is from the perl version of Textile.
        for qtag, htmltag, redict in qtags:
            self.res.update(redict)
            p = re.compile(r'''(?:                          #
                                   ^                        # Start of string
                                   |                        #
                                   (?<=[\s>'"])             # Whitespace, end of tag, quotes
                                   |                        #
                                   (?P<pre>[{[])            # Surrounded by [ or {
                                   |                        #
                                   (?<=%(punct)s)           # Punctuation
                               )                            #
                               %(qf)s                       # opening tag
                               %(qattr)s                    # attributes
                               (?P<text>[^%(cls)s\s].*?)    # text
                               (?<=\S)                      # non-whitespace
                               %(qf)s                       # 
                               (?:                          #
                                   $                        # End of string
                                   |                        #
                                   (?P<post>[\]}])          # Surrounded by ] or }
                                   |                        # 
                                   (?=%(punct)s{1,2}|\s)    # punctuation
                                )                           #
                             ''' % self.res, re.VERBOSE)

            def _replace(m):
                c = m.groupdict('')

                attributes = self.parse_params(c['parameters'])
                open_tag  = self.build_open_tag(htmltag, attributes) 
                close_tag = '</%s>' % htmltag

                # Replace < and > inside <code></code>.
                if htmltag == 'code':
                    c['text'] = c['text'].replace('<', '&lt;')
                    c['text'] = c['text'].replace('>', '&gt;')
         
                return open_tag + c['text'] + close_tag

            text = p.sub(_replace, text)

        return text


    def images(self, text):
        """Process images.

        This function process images tags, with or without links. Images
        can have vertical and/or horizontal alignment, and can be resized
        unefficiently using width and height tags.

        ---
        h1. Images

        An image is generated by enclosing the image source in @!@:

        pre. !/path/to/image!

        You may optionally specify an alternative text for the image, which
        will also be used as its title:

        pre. !image.jpg (Nice picture)!

        Becomes:

        pre. <p><img src="image.jpg" alt="Nice picture" title="Nice picture" /></p>

        If you want to make the image point to a link, simply append a
        comma and the URL(Universal Republic of Love) to the image:

        pre. !image.jpg!:http://diveintopython.org

        Images can also be resized. These are all equivalent:

        pre. !image.jpg 10x20!
        !image.jpg 10w 20h!
        !image.jpg 20h 10w!

        The image @image.jpg@ will be resized to width 10 and height 20.

        Modifiers to the @<img>@ tag go after the opening @!@:

        pre. !(class#id)^image.jpg!

        Allowed modifiers include:
        
        dl. &lt;:Align the image to the left (causes the image to float if CSS options are enabled). 
        &gt;:Align the image to the right (causes the image to float if CSS options are enabled). 
        - (dash):Aligns the image to the middle. 
        ^:Aligns the image to the top. 
        ~ (tilde):Aligns the image to the bottom. 
        {style rule}:Applies a CSS style rule to the image. 
        (class) or (#id) or (class#id):Applies a CSS class and/or id to the image. 
        ( (one or more):Pads 1em on the left for each '(' character. 
        ) (one or more):Pads 1em on the right for each ')' character. 

        Images receive the class "top" when using top alignment, "bottom" 
        for bottom alignment and "middle" for middle alignment.
        """
        # Compile the beast.
        p = re.compile(r'''\!               # Opening !
                           %(iattr)s        # Image attributes
                           (?P<src>%(url)s) # Image src
                           \s?              # Optional whitesapce
                           (                #
                               \(           #
                               (?P<alt>.*?) # Optional (alt) attribute
                               \)           #
                           )?               #
                           \s?              # Optional whitespace
                           %(resize)s       # Resize parameters
                           \!               # Closing !
                           (                # Optional link
                               :            #    starts with ':'
                               (?P<link>    #    
                               %(url)s      #    link HREF
                               )            #
                           )?               #
                        ''' % self.res, re.VERBOSE)

        for m in p.finditer(text):
            c = m.groupdict('')

            # Build the parameters for the <img /> tag.
            attributes = self.parse_params(c['parameters'], align_type='image')
            attributes.update(c)
            if attributes['alt']:
                attributes['title'] = attributes['alt']

            # Append height and width.
            attributes['width'] = m.groups()[5] or m.groups()[7] or m.groups()[10]
            attributes['height'] = m.groups()[6] or m.groups()[8] or m.groups()[9]

            # Create the image tag.
            tag = self.image(attributes)

            text = text.replace(m.group(), tag)
        
        return text


    def image(self, attributes):
        """Process each image.

        This method builds the <img> tag for each image in the text. It's
        separated from the 'images' method so it can be easily overriden when
        subclassing Textiler. Useful if you want to download and/or process
        the images, for example.
        """
        link = attributes['link']
        del attributes['link']
        del attributes['parameters']

        # Build the tag.
        tag = self.build_open_tag('img', attributes, single=1)

        if link:
            href = preg_replace('&(?!(#|amp))', '&amp;', link)
            tag = '<a href="%s">%s</a>' % (href, tag)

        return tag


    def links(self, text):
        """Process links.

        This function is responsible for processing links. It has
        some nice shortcuts to Google, Amazon and IMDB queries.

        ---
        h1. Links

        A links is done the following way:

        pre. "This is the text link":http://example.com

        The result from this markup is:

        pre. <p><a href="http://example.com">This is the text link</a></p>

        You can add an optional @title@ attribute:

        pre. "This is the text link(This is the title)":http://example.com

        The link can be customised as well:

        pre. "(nospam)E-mail me please":mailto:someone@example.com

        You can use either single or double quotes. They must be enclosed in
        whitespace, punctuation or brackets:

        pre. You["gotta":http://example.com]seethis!

        If you are going to reference the same link a couple of times, you
        can define a lookup list anywhere on your document:

        pre. [python]http://www.python.org

        Links to the Python website can then be defined the following way:

        pre. "Check this":python

        There are also shortcuts for Amazon, IMDB(Internet Movie DataBase) and
        Google queries:

        pre. "Has anyone seen this guy?":imdb:Stephen+Fry
        "Really nice book":amazon:Goedel+Escher+Bach
        "PyBlosxom":google
        ["Using Textile and Blosxom with Python":google:python blosxom textile]

        Becomes:

        pre. <a href="http://www.imdb.com/Find?for=Stephen+Fry">Has anyone seen this guy?</a>
        <a href="http://www.amazon.com/exec/obidos/external-search?index=blended&amp;keyword=Goedel+Escher+Bach">Really nice book</a>
        <a href="http://www.google.com/search?q=PyBlosxom">PyBlosxom</a>
        <a href="http://www.google.com/search?q=python+blosxom+textile">Using Textile and Blosxom with Python</a>
        """
        linkres = [r'''\[                           # [
                       (?P<quote>"|')               # Opening quotes
                       %(lattr)s                    # Link attributes
                       (?P<text>[^"]+?)             # Link text
                       \s?                          # Optional whitespace
                       (?:\((?P<title>[^\)]+?)\))?  # Optional (title)
                       (?P=quote)                   # Closing quotes
                       :                            # :
                       (?P<href>[^\]]+)             # HREF
                       \]                           # ]
                    ''' % self.res,
                   r'''(?P<quote>"|')               # Opening quotes
                       %(lattr)s                    # Link attributes
                       (?P<text>[^"]+?)             # Link text
                       \s?                          # Optional whitespace
                       (?:\((?P<title>[^\)]+?)\))?  # Optional (title)
                       (?P=quote)                   # Closing quotes
                       :                            # :
                       (?P<href>%(url)s)            # HREF
                    ''' % self.res]

        for linkre in linkres:
            p = re.compile(linkre, re.VERBOSE)
            for m in p.finditer(text):
                c = m.groupdict('')

                attributes = self.parse_params(c['parameters'])
                attributes['title'] = c['title'].replace('"', '&quot;')

                # Search lookup list.
                link = self._links.get(c['href'], None) or c['href']

                # Hyperlinks for Amazon, IMDB and Google searches.
                parts = link.split(':', 1)
                proto = parts[0]
                if len(parts) == 2:
                    query = parts[1]
                else:
                    query = c['text']

                query = query.replace(' ', '+')

                # Look for smart search.
                if self.searches.has_key(proto):
                    link = self.searches[proto] % query
                
                # Fix URL.
                attributes['href'] = preg_replace('&(?!(#|amp))', '&amp;', link)

                open_tag = self.build_open_tag('a', attributes)
                close_tag = '</a>'

                repl = open_tag + c['text'] + close_tag

                text = text.replace(m.group(), repl)

        return text


    def format(self, text):
        """Text formatting.

        This function basically defines the order on which the 
        formatting is applied.
        """
        text = self.qtags(text)
        text = self.images(text)
        text = self.links(text)
        text = self.acronym(text)
        text = self.glyphs(text)

        return text


    def inline(self, text):
        """Inline formatting.

        This function calls the formatting on the inline text,
        taking care to avoid the escaped parts.

        ---
        h1. Inline 

        Inline formatting is applied within a block of text.
        """
        if not re.search(r'''==(.*?)==''', text):
            text = self.format(text)

        else:
            lines = []
            # Else split the text into an array at <>.
            for line in re.split('(==.*?==)', text):
                if not re.match('==.*?==', line):
                    line = self.format(line)
                else:
                    line = line[2:-2]

                lines.append(line)
            
            text = ''.join(lines)

        return text
            

def textile(text, **args):
    """This is Textile.

    Generates XHTML from a simple markup developed by Dean Allen.

    This function should be called like this:
    
        textile(text, head_offset=0, validate=0, sanitize=0,
                encoding='latin-1', output='ASCII')
    """
    return Textiler(text).process(**args)


if __name__ == '__main__':
    print textile('tell me about textile.', head_offset=1)
