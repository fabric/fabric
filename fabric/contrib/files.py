"""
Module providing easy API for working with remote files and folders.
Changelog : 2012-07 FSo deeply improved functions :
- creating wrap_regex() to prepare strings for egrep, sed, ...
- using this function in all others needing string escaping
- change append() behavior to process only a line and not a text.
  Seems to be easier to do an append() eventually with specific
  parameters on each line we want to add.
  Replaced ``Partial`` keyword by ``exact_match``  
- created insert() function to insert a line before or after a
  line matching a regex
- created delete() function to do what it seems :)
"""

from __future__ import with_statement

import hashlib
import tempfile
import re
import os
from StringIO import StringIO

from fabric.api import *


def exists(path, use_sudo=False, verbose=False):
    """
    Return True if given path exists on the current remote host.

    If ``use_sudo`` is True, will use `sudo` instead of `run`.

    `exists` will, by default, hide all output (including the run line, stdout,
    stderr and any warning resulting from the file not existing) in order to
    avoid cluttering output. You may specify ``verbose=True`` to change this
    behavior.
    """
    func = use_sudo and sudo or run
    cmd = 'test -e "$(echo %s)"' % path
    # If verbose, run normally
    if verbose:
        with settings(warn_only=True):
            return not func(cmd).failed
    # Otherwise, be quiet
    with settings(hide('everything'), warn_only=True):
        return not func(cmd).failed


def first(*args, **kwargs):
    """
    Given one or more file paths, returns first one found, or None if none
    exist. May specify ``use_sudo`` and ``verbose`` which are passed to `exists`.
    """
    for directory in args:
        if exists(directory, **kwargs):
            return directory


def upload_template(filename, destination, context=None, use_jinja=False,
    template_dir=None, use_sudo=False, backup=True, mirror_local_mode=False,
    mode=None):
    """
    Render and upload a template text file to a remote host.

    ``filename`` should be the path to a text file, which may contain `Python
    string interpolation formatting
    <http://docs.python.org/release/2.5.4/lib/typesseq-strings.html>`_ and will
    be rendered with the given context dictionary ``context`` (if given.)

    Alternately, if ``use_jinja`` is set to True and you have the Jinja2
    templating library available, Jinja will be used to render the template
    instead. Templates will be loaded from the invoking user's current working
    directory by default, or from ``template_dir`` if given.

    The resulting rendered file will be uploaded to the remote file path
    ``destination``.  If the destination file already exists, it will be
    renamed with a ``.bak`` extension unless ``backup=False`` is specified.

    By default, the file will be copied to ``destination`` as the logged-in
    user; specify ``use_sudo=True`` to use `sudo` instead.

    The ``mirror_local_mode`` and ``mode`` kwargs are passed directly to an
    internal `~fabric.operations.put` call; please see its documentation for
    details on these two options.

    .. versionchanged:: 1.1
        Added the ``backup``, ``mirror_local_mode`` and ``mode`` kwargs.
    """
    func = use_sudo and sudo or run
    # Normalize destination to be an actual filename, due to using StringIO
    with settings(hide('everything'), warn_only=True):
        if func('test -d %s' % destination).succeeded:
            sep = "" if destination.endswith('/') else "/"
            destination += sep + os.path.basename(filename)

    # Use mode kwarg to implement mirror_local_mode, again due to using
    # StringIO
    if mirror_local_mode and mode is None:
        mode = os.stat(filename).st_mode
        # To prevent put() from trying to do this
        # logic itself
        mirror_local_mode = False

    # Process template
    text = None
    if use_jinja:
        try:
            from jinja2 import Environment, FileSystemLoader
            jenv = Environment(loader=FileSystemLoader(template_dir or '.'))
            text = jenv.get_template(filename).render(**context or {})
        except ImportError:
            import traceback
            tb = traceback.format_exc()
            abort(tb + "\nUnable to import Jinja2 -- see above.")
    else:
        with open(filename) as inputfile:
            text = inputfile.read()
        if context:
            text = text % context

    # Back up original file
    if backup and exists(destination):
        func("cp %s{,.bak}" % destination)

    # Upload the file.
    put(
        local_path=StringIO(text),
        remote_path=destination,
        use_sudo=use_sudo,
        mirror_local_mode=mirror_local_mode,
        mode=mode
    )


def sed(filename, before, after, limit='', use_sudo=False, backup='.bak',
    flags=''):
    """
    Run a search-and-replace on ``filename`` with given regex patterns.

    Equivalent to ``sed -i<backup> -r -e "/<limit>/ s/<before>/<after>/<flags>g
    <filename>"``. Setting ``backup`` to an empty string will, disable backup
    file creation.
    ``limit`` is a string to match when searching for lines on which sed must act,
    instead of searching ``before`` in each line of the file (default: all lines).

    For convenience, ``before`` and ``after`` will automatically escape forward
    slashes, single quotes and parentheses for you, so you don't need to
    specify e.g.  ``http:\/\/foo\.com``, instead just using ``http://foo\.com``
    is fine.

    If ``use_sudo`` is True, will use `sudo` instead of `run`.

    `sed` will pass ``shell=False`` to `run`/`sudo`, in order to avoid problems
    with many nested levels of quotes and backslashes.

    Other options may be specified with sed-compatible regex flags -- for
    example, to make the search and replace case insensitive, specify
    ``flags="i"``. The ``g`` flag is always specified regardless, so you do not
    need to remember to include it when overriding this parameter.

    .. versionadded:: 1.1
        The ``flags`` parameter.
    .. versionchanged:: - FSo 2012/07
        See headlines of files.py
    """
    func = use_sudo and sudo or run
    if limit:
        limit = r'/%s/ ' % limit
    # Test the OS because of differences between sed versions

    with hide('running', 'stdout'):
        platform = run("uname")
    if platform in ('NetBSD', 'OpenBSD', 'QNX'):
        # Attempt to protect against failures/collisions
        hasher = hashlib.sha1()
        hasher.update(env.host_string)
        hasher.update(filename)
        tmp = "/tmp/%s" % hasher.hexdigest()
        # Use temp file to work around lack of -i
        expr = r"""cp -p %(filename)s %(tmp)s \
&& sed -r -e '%(limit)ss/%(before)s/%(after)s/%(flags)sg' %(filename)s > %(tmp)s \
&& cp -p %(filename)s %(filename)s%(backup)s \
&& mv %(tmp)s %(filename)s"""
        command = expr % locals()
    else:
        expr = r"sed -i%s -r -e '%ss/%s/%s/%sg' %s"
        command = expr % (backup, limit, before, after, flags, filename)
    return func(command, shell=False)


def uncomment(filename, regex, exact_match=True, use_sudo=False, char='#', backup='.bak'):
    """
    Attempt to uncomment all lines in ``filename`` matching ``regex``.

    The default comment delimiter is `#` and may be overridden by the ``char``
    argument.

    This function uses the `sed` function, and will accept the same
    ``use_sudo`` and ``backup`` keyword arguments that `sed` does.

    `uncomment` will remove a single whitespace character following the comment
    character, if it exists, but will preserve all preceding whitespace.  For
    example, ``# foo`` would become ``foo`` (the single space is stripped) but
    ``    # foo`` would become ``    foo`` (the single space is still stripped,
    but the preceding 4 spaces are not.)

    .. versionchanged:: - FSo 2012/07
        See headlines of files.py
    """
    return sed(
        filename,
        before=r'^([[:space:]]*)%s[[:space:]]?' % char,
        after=r'\1',
        limit=wrap_regex(regex,exact_match=exact_match),
        use_sudo=use_sudo,
        backup=backup
    )


def comment(filename, regex, exact_match=True, use_sudo=False, char='#', backup='.bak'):
    """
    Attempt to comment out all lines in ``filename`` matching ``regex``.

    The default commenting character is `#` and may be overridden by the
    ``char`` argument.

    This function uses the `sed` function, and will accept the same
    ``use_sudo`` and ``backup`` keyword arguments that `sed` does.

    `comment` will prepend the comment character to the beginning of the line,
    so that lines end up looking like so::

        this line is uncommented
        #this line is commented
        #   this line is indented and commented

    In other words, comment characters will not "follow" indentation as they
    sometimes do when inserted by hand. Neither will they have a trailing space
    unless you specify e.g. ``char='# '``.

    .. note::

        In order to preserve the line being commented out, this function will
        wrap your ``regex`` argument in parentheses, so you don't need to. It
        will ensure that any preceding/trailing ``^`` or ``$`` characters are
        correctly moved outside the parentheses. For example, calling
        ``comment(filename, r'^foo$')`` will result in a `sed` call with the
        "before" regex of ``r'^(foo)$'`` (and the "after" regex, naturally, of
        ``r'#\\1'``.)

    .. versionchanged:: - FSo 2012/07
        See headlines of files.py
    """
    return sed(
        filename,
        before=wrap_regex(regex,exact_match=exact_match),
        after=r'%s\1' % char,
        use_sudo=use_sudo,
        backup=backup
    )


def contains(filename, string2add, exact_match=False, use_sudo=False):
    """
    Return True if ``filename`` contains ``text`` (which may be a regex.)

    By default, this function will consider a partial line match (i.e. where
    ``text`` only makes up part of the line it's on). Specify ``exact_match=True`` to
    change this behavior so that only a line containing exactly ``text``
    results in a True return value.

    This function leverages ``egrep`` on the remote end (so it may not follow
    Python regular expression syntax perfectly), and skips the usual outer
    ``env.shell`` wrapper that most commands execute with.

    If ``use_sudo`` is True, will use `sudo` instead of `run`.

    .. versionchanged:: 1.0
        Swapped the order of the ``filename`` and ``text`` arguments to be
        consistent with other functions in this module.
    .. versionchanged:: 1.4
        Updated the regular expression related escaping to try and solve
        various corner cases.
    .. versionchanged:: 1.4
        Added ``escape`` keyword argument.
    .. versionchanged:: - FSo 2012/07
        See headlines of files.py
    """
    func = use_sudo and sudo or run
    string2add = wrap_regex(string2add, exact_match=exact_match)
    with settings(hide('everything'), warn_only=True):
        egrep_cmd = 'egrep "%s" "%s"' % (string2add, filename)
        return func(egrep_cmd, shell=False).succeeded


def append(filename, string2add, if_exist=False, exact_match=True, use_sudo=False):
    """
    Append string ``string2add`` to ``filename``.

    If ``string2add`` is already found in ``filename`` and ``if_exist`` is False, the
    append is not run, and None is returned immediately. Otherwise, the given string
    is appended to the end of the given ``filename`` via e.g. ``echo '$string2add' >> $filename``.

    The test for whether ``string2add`` already exists defaults to a full line match,
    e.g. ``^<string2add>$``, default given by the keyword ``exact_match``. This seems to be
    the most sensible approach for the "append line to a file" use case. You may override this
    and force partial searching (e.g. just ``<string2add>``) by specifying ``exact_match=False``.

    If ``use_sudo`` is True, will use `sudo` instead of `run`.

    .. versionchanged:: 0.9.1
        Added the ``partial`` keyword argument.
    .. versionchanged:: 1.0
        Swapped the order of the ``filename`` and ``text`` arguments to be
        consistent with other functions in this module.
    .. versionchanged:: 1.0
        Changed default value of ``partial`` kwarg to be ``False``.
    .. versionchanged:: 1.4
        Updated the regular expression related escaping to try and solve
        various corner cases.
    .. versionchanged:: - FSo 2012/07
        See headlines of files.py
    """
    func = use_sudo and sudo or run
    if not (not if_exist
        and contains(filename, string2add, exact_match=exact_match, use_sudo=use_sudo)):
       func("echo '%s' >> %s" % (string2add, filename))

def delete(filename, regex, exact_match=False, use_sudo=True, backup='.bak'):
    """
    Delete a line in ``filename`` when matching given regex patterns.

    Equivalent to ``sed -i<backup> -r -e "<lineno>d <filename>"``.

    If ``exact_match`` is True (default), delete any line matching the regex.
    Otherwise delete any line CONTAINING the regex.

    If ``use_sudo`` is True, will use `sudo` instead of `run`.

    .. note::
        ONLY TESTED ON LINUX BOXES
    .. note::
        In order to preserve the wrong line being deleted, this function will
        wrap your ``regex`` argument in parentheses, so you don't need to. It
        will ensure that any preceding/trailing ``^`` or ``$`` characters are
        correctly moved outside the parentheses.
    .. note::
        As the line number change any time we delete a line, we can't implement
        a recursive deletion of many lines. The function must be run again to
        delete more than one matching line.

    TODO : ``reverse`` implementation (searching from the bottom of file)
    TODO : ``count`` possible ? (deleting a ``count`` number of matching lines)

    .. versionchanged:: - FSo 2012/07
        See headlines of files.py
    """

    func = use_sudo and sudo or run
    expr = r"sed -n -r -e '/%s/=' %s"
    command = expr % (wrap_regex(regex,exact_match=exact_match), filename)
    linenos = func(command, shell=False)
    linenos = linenos.split("\r\n")
    if linenos.count('') > 0:
        linenos.remove('')

    if linenos:
        expr = r"sed -i%s '%sd' %s"
        command = expr % (backup, linenos[0], filename)
        return func(command)

def insert(filename, regex, string2add, if_exist=False, exact_match=True, before=False,
    use_sudo=False, backup='.bak'):
    """
    Insert a line into ``filename`` before or after a line matching giveno
    regex patterns.

    If ``before`` is True, the line is added before the matching line, else after.

    If ``regex`` is already found in ``filename`` and ``if_exist`` is False, the
    insert is not run, and None is returned immediately. Otherwise (string not found
    and/or ``if_exist=True``), the given string is inserted in the given ``filename``.

    If ``use_sudo`` is True, will use `sudo` instead of `run`.

    .. note::
        ONLY TESTED ON LINUX BOXES
    .. note::
        In order to preserve the wrong line being deleted, this function will
        wrap your ``regex`` argument in parentheses, so you don't need to. It
        will ensure that any preceding/trailing ``^`` or ``$`` characters are
        correctly moved outside the parentheses.
    .. note::
        As the regex is always found in the first matching line, we can't
        implement more than one insertion because it would be inserted always
        around the first line found.

    TODO : ``reverse`` implementation (searching from the bottom of file)

    .. versionchanged:: - FSo 2012/07
        See headlines of files.py
    """

    func = use_sudo and sudo or run
    regex = wrap_regex(regex,exact_match=exact_match)
    expr = r"sed -n -r -e '/%s/=' %s"
    command = expr % (regex, filename)
    linenos = func(command, shell=False)
    linenos = linenos.split("\r\n")
    if linenos.count('') > 0:
        linenos.remove('')
    if (linenos and not (not if_exist
       and contains(filename, string2add, exact_match=exact_match, use_sudo=use_sudo))):
        if before:
            expr = r"sed -i%s -r -e '%s i\%s' %s"
        else:
            expr = r"sed -i%s -r -e '%s a\%s' %s"
        command = expr % (backup, linenos[0], wrap_regex(string2add), filename)
        return func(command)

def wrap_regex(regex,exact_match=False):
    """
    Escape ``text`` to handle or not special chars with egrep, sed, ...

    if ``exact_match`` is true, add ``^`` at the beginning and ``$``
    at the end of the string

    .. versionchanged:: - FSo 2012/07
        See headlines of files.py
    """
    carot, dollar = '^', '$'
    if regex.startswith('^'):
       regex = regex[1:]
    if regex.endswith('$'):
       regex = regex[:-1]
#    regex = re.escape(text)
    rx = re.compile('([(){}\[\]*$+/])')
    regex = rx.sub('\\\\\\1', regex)
    regex = "%s(%s)%s" % (carot, regex, dollar) if exact_match else regex
    return regex

