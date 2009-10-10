===================
Defining host lists
===================


Defining hosts
----------------

Hosts, in this context, refer to what are also called "host strings": Python
strings referring to a specific user, hostname and port combination, in the
format ``user@hostname:port``. User and/or port (and the associated ``@`` or
``:``) may be omitted, and will be filled by the executing user's local
username, and/or port 22, respectively.

Thus, ``admin@foo.com:222``, ``deploy@website`` and ``nameserver1`` could all
be valid host strings.

Defining roles
----------------

Roles are simply string identifiers mapping to lists of host strings. This
mapping is defined as a dictionary, ``env.roledefs``, and must be modified by a
fabfile in order to be referenced, e.g.::

    from fabric.api import env

    env.roledefs['webservers'] = ['www1', 'www2', 'www3']

Since this dictionary is naturally empty by default, you may also opt to
re-assign to it without fear of losing any information (provided you aren't
loading other fabfiles which also modify it, of course)::

    from fabric.api import env

    env.roledefs = {
        'web': ['www1', 'www2', 'www3'],
        'dns': ['ns1', 'ns2']
    }


How host lists are constructed
------------------------------

Construction of a command's host list follows a strict order of precedence, so
that the first available set of hosts in the list wins and the rest of the
checks are skipped. Hosts and roles may be specified simultaneously and will be
combined; see :ref:`combining-host-lists` for details.

The lookup order is as follows:

#. Per-command hosts or roles specified via the command line (e.g. ``fab
   foo:hosts='a;b;c'``)
#. Hosts specified via the `~fabric.decorators.hosts` and
   `~fabric.decorators.roles` decorators
#. The values of ``env.hosts`` and/or ``env.roles`` (both being lists of
   strings, host strings or role names respectively) which may be set via:

    * The command-line options ``--hosts`` and ``--roles`` (using
      comma-separated lists of strings)
    * Python code operating on ``env`` within your fabfile (which will append
      to or overwrite anything set on the command line)

    .. note:: 
        You may set either of these at module level, in which case the given
        list will apply globally to all commands (unless overridden in one of
        the previous ways.)

.. _combining-host-lists:

Combining host lists
--------------------

There is no "unionizing" of hosts between the various sources mentioned above.
If a global host list contains hosts A, B and C, and a per-function (e.g.
via `~fabric.decorators.hosts`) host list is set to just hosts B and C, that
function will **not** execute on host A.

However, `~fabric.decorators.hosts` and `~fabric.decorators.roles` **will**
result in the union of their contents as the final host list. In the following
example, the resulting host list will be ``['a', 'b', 'c']``::


    env.roledefs = {'role1': ['b', 'c']}

    @hosts('a', 'b')
    @roles('role1')
    def my_func():
        pass


