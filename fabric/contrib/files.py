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


def upload_template(template, context, destination):
    """
    Render and upload a template text file to a remote host.

    ``template`` should be the path to a text file, which may contain Python
    string interpolation formatting and will be rendered with the given context
    dictionary ``context``.
    
    The resulting rendered file will be uploaded to the remote file path
    ``destination`` (which should include the desired remote filename.)
    """
    with open(template) as inputfile:
        text = inputfile.read()
    with tempfile.NamedTemporaryFile() as output:
        output.write(text % context)
        output.flush()
        put(output.name, "/tmp/" + template)
    sudo("mv /tmp/%s %s" % (template, destination + template))


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
    """
    func = use_sudo and sudo or run
    expr = r'sed -i%s -r -e "%ss/%s/%s/g" %s'
    before = before.replace('/', r'\/')
    after = after.replace('/', r'\/')
    if limit:
        limit = r'/%s/ ' % limit
    command = expr % (backup, limit, before, after, filename)
    return func(command)


def uncomment(filename, regex, use_sudo=False, char='#', backup='.bak'):
    """
    Attempt to uncomment all lines in ``filename`` matching ``regex``.

    Uses `run`, but will use `sudo` if the ``use_sudo`` argument is True.

    The default comment delimiter is `#` and may be overridden by the ``char``
    argument.

    By default, ``-i.bak`` is passed to ``sed``, and this may be overridden by
    setting the ``backup`` argument (which defaults to ``.bak``).

    This function will remove a single whitespace character following the
    comment character, if it exists, but will preserve all preceding whitespace.
    For example, ``# foo`` would become ``foo`` (the single space is stripped)
    but ``    # foo`` would become ``    foo`` (the single space is still
    stripped, but the preceding 4 spaces are not.)
    """
    return sed(filename,
        before=r'^([[:space:]]*)%s[[:space:]]?' % char,
        after=r'\1',
        limit=regex,
        use_sudo=use_sudo,
        backup=backup
    )


def contains(text, filename, exact=False, use_sudo=False):
    """
    Return True if ``filename`` contains ``text``.

    By default, this function will consider a partial line match (i.e. where the
    given text only makes up part of the line it's on). Specify ``exact=True``
    to change this behavior so that only a line containing exactly ``text``
    results in a True return value.

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

    If ``text`` is already found as a discrete line in ``filename``, the append is
    not run, and None is returned immediately. Otherwise, the given text is
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
