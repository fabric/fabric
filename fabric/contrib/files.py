"""
Module providing easy API for working with remote files and folders.
"""

from __future__ import with_statement

import tempfile

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
    cmd = 'ls -d --color=never %s' % path
    # If verbose, run normally
    if verbose:
        return func(cmd)
    # Otherwise, be quiet
    with settings(
        hide('warnings', 'running', 'stdout', 'stderr'),
        warn_only=True
    ):
        return func(cmd)


def first(*args, **kwargs):
    """
    Given one or more file paths, returns first one found, or None if none
    exist. May specify ``use_sudo`` which is passed to `exists`.
    """
    for directory in args:
        if not kwargs.get('use_sudo'):
            if exists(directory, sudo=False):
                return directory
        else:
            if exists(directory):
                return directory


def upload_template(filename, destination, context=None, use_sudo=False):
    """
    Render and upload a template text file to a remote host.

    ``filename`` should be the path to a text file, which may contain Python
    string interpolation formatting and will be rendered with the given context
    dictionary ``context`` (if given.)
    
    The resulting rendered file will be uploaded to the remote file path
    ``destination`` (which should include the desired remote filename.)

    By default, the file will be copied to ``destination`` as the logged-in
    user; specify ``use_sudo=True`` to use `sudo` instead.
    """
    with open(filename) as inputfile:
        text = inputfile.read()
    with tempfile.NamedTemporaryFile() as output:
        if context:
            text = text % context
        output.write(text)
        output.flush()
        put(output.name, "/tmp/" + filename)
    func = use_sudo and sudo or run
    # Crappy sanity check pending a real os.path.join type function that honors
    # the remote system's join character.
    if not destination.endswith('/'):
        destination += '/'
    destination = destination + filename
    # Back up any original file
    if exists(destination):
        func("cp %s %s.bak" % (destination, destination))
    # Actually move uploaded template to destination
    func("mv /tmp/%s %s" % (filename, destination))


def sed(filename, before, after, limit='', use_sudo=False, backup='.bak'):
    """
    Run a search-and-replace on ``filename`` with given regex patterns.

    Equivalent to ``sed -i<backup> -e "/<limit>/ s/<before>/<after>/g
    <filename>"``.

    For convenience, ``before`` and ``after`` will automatically escape forward
    slashes (and **only** forward slashes) for you, so you don't need to
    specify e.g.  ``http:\/\/foo\.com``, instead just using ``http://foo\.com``
    is fine.

    If ``use_sudo`` is True, will use `sudo` instead of `run`.

    `sed` will pass ``shell=False`` to `run`/`sudo`, in order to avoid problems
    with many nested levels of quotes and backslashes.
    """
    func = use_sudo and sudo or run
    expr = r"sed -i%s -r -e '%ss/%s/%s/g' %s"
    before = before.replace('/', r'\/')
    after = after.replace('/', r'\/')
    if limit:
        limit = r'/%s/ ' % limit
    command = expr % (backup, limit, before, after, filename)
    return func(command, shell=False)


def uncomment(filename, regex, use_sudo=False, char='#', backup='.bak'):
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
    """
    return sed(
        filename,
        before=r'^([[:space:]]*)%s[[:space:]]?' % char,
        after=r'\1',
        limit=regex,
        use_sudo=use_sudo,
        backup=backup
    )


def comment(filename, regex, use_sudo=False, char='#', backup='.bak'):
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
    """
    carot = ''
    dollar = ''
    if regex.startswith('^'):
        carot = '^'
        regex = regex[1:]
    if regex.endswith('$'):
        dollar = '$'
        regex = regex[:1]
    regex = "%s(%s)%s" % (carot, regex, dollar)
    return sed(
        filename,
        before=regex,
        after='%s\1' % char,
        use_sudo=use_sudo,
        backup=backup
    )


def contains(text, filename, exact=False, use_sudo=False):
    """
    Return True if ``filename`` contains ``text``.

    By default, this function will consider a partial line match (i.e. where
    the given text only makes up part of the line it's on). Specify
    ``exact=True`` to change this behavior so that only a line containing
    exactly ``text`` results in a True return value.

    Double-quotes in either ``text`` or ``filename`` will be automatically
    backslash-escaped in order to behave correctly during the remote shell
    invocation.

    If ``use_sudo`` is True, will use `sudo` instead of `run`.
    """
    func = use_sudo and sudo or run
    if exact:
        text = "^%s$" % text
    return func('egrep "%s" "%s"' % (
        text.replace('"', r'\"'),
        filename.replace('"', r'\"')
    ))


def append(text, filename, use_sudo=False):
    """
    Append ``text`` to ``filename``.

    If ``text`` is already found as a discrete line in ``filename``, the append
    is not run, and None is returned immediately. Otherwise, the given text is
    appended to the end of the given ``filename`` via e.g. ``echo '$text' >>
    $filename``.

    Because ``text`` is single-quoted, single quotes will be transparently 
    backslash-escaped.

    If ``use_sudo`` is True, will use `sudo` instead of `run`.
    """
    func = use_sudo and sudo or run
    with setenv(warn_only=True):
        if contains(text, filename, use_sudo=use_sudo):
            return None
    return func("echo '%s' >> %s" % (text.replace("'", r'\''), filename))
