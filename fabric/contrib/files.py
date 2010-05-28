"""
Module providing easy API for working with remote files and folders.
"""

from __future__ import with_statement

import tempfile
import re
import os

from fabric.api import run, sudo, settings, put, hide, abort


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
    cmd = 'test -e "%s"' % path
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
    exist. May specify ``use_sudo`` which is passed to `exists`.
    """
    for directory in args:
        if not kwargs.get('use_sudo'):
            if exists(directory, sudo=False):
                return directory
        else:
            if exists(directory):
                return directory


def upload_template(filename, destination, context=None, use_jinja=False,
    template_dir=None, use_sudo=False):
    """
    Render and upload a template text file to a remote host.

    ``filename`` should be the path to a text file, which may contain Python
    string interpolation formatting and will be rendered with the given context
    dictionary ``context`` (if given.)

    Alternately, if ``use_jinja`` is set to True and you have the Jinja2
    templating library available, Jinja will be used to render the template
    instead. Templates will be loaded from the invoking user's current working
    directory by default, or from ``template_dir`` if given.
    
    The resulting rendered file will be uploaded to the remote file path
    ``destination`` (which should include the desired remote filename.) If the
    destination file already exists, it will be renamed with a ``.bak``
    extension.

    By default, the file will be copied to ``destination`` as the logged-in
    user; specify ``use_sudo=True`` to use `sudo` instead.
    """
    basename = os.path.basename(filename)
    temp_destination = '/tmp/' + basename

    # This temporary file should not be automatically deleted on close, as we
    # need it there to upload it (Windows locks the file for reading while open).
    tempfile_fd, tempfile_name = tempfile.mkstemp()
    output = open(tempfile_name, "w+b")
    # Init
    text = None
    if use_jinja:
        try:
            from jinja2 import Environment, FileSystemLoader
            jenv = Environment(loader=FileSystemLoader(template_dir or '.'))
            text = jenv.get_template(filename).render(**context or {})
        except ImportError, e:
            abort("tried to use Jinja2 but was unable to import: %s" % e)
    else:
        with open(filename) as inputfile:
            text = inputfile.read()
        if context:
            text = text % context
    output.write(text)
    output.close()

    # Upload the file.
    put(tempfile_name, temp_destination)
    os.close(tempfile_fd)
    os.remove(tempfile_name)

    func = use_sudo and sudo or run
    # Back up any original file (need to do figure out ultimate destination)
    to_backup = destination
    with settings(hide('everything'), warn_only=True):
        # Is destination a directory?
        if func('test -f %s' % to_backup).failed:
            # If so, tack on the filename to get "real" destination
            to_backup = destination + '/' + basename
    if exists(to_backup):
        func("cp %s %s.bak" % (to_backup, to_backup))
    # Actually move uploaded template to destination
    func("mv %s %s" % (temp_destination, destination))


def sed(filename, before, after, limit='', use_sudo=False, backup='.bak'):
    """
    Run a search-and-replace on ``filename`` with given regex patterns.

    Equivalent to ``sed -i<backup> -r -e "/<limit>/ s/<before>/<after>/g
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
        after=r'%s\1' % char,
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
    with settings(hide('everything'), warn_only=True):
        return func('egrep "%s" "%s"' % (
            text.replace('"', r'\"'),
            filename.replace('"', r'\"')
        ))


def append(text, filename, use_sudo=False, partial=True):
    """
    Append string (or list of strings) ``text`` to ``filename``.

    When a list is given, each string inside is handled independently (but in
    the order given.)

    If ``text`` is already found in ``filename``, the append is not run, and
    None is returned immediately. Otherwise, the given text is appended to the
    end of the given ``filename`` via e.g. ``echo '$text' >> $filename``.

    The test for whether ``text`` already exists defaults to being partial
    only, as in ``^<text>``. Specifying ``partial=False`` will change the
    effective regex to ``^<text>$``.

    Because ``text`` is single-quoted, single quotes will be transparently 
    backslash-escaped.

    If ``use_sudo`` is True, will use `sudo` instead of `run`.

    .. versionchanged:: 0.9.1
        Added the ``partial`` keyword argument.
    """
    func = use_sudo and sudo or run
    # Normalize non-list input to be a list
    if isinstance(text, str):
        text = [text]
    for line in text:
        if (contains('^' + re.escape(line) + ('' if partial else '$'), filename, use_sudo=use_sudo)
            and line):
            continue
        func("echo '%s' >> %s" % (line.replace("'", r'\''), filename))
