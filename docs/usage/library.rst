===========
Library Use
===========

Fabric's primary use case is via fabfiles and the :doc:`fab </usage/fab>` tool,
and this is reflected in much of the documentation. However, Fabric's internals
are written in such a manner as to be easily used without ``fab`` or fabfiles
at all -- this document will show you how.

There's really only a couple of considerations one must keep in mind, when
compared to writing a fabfile and using ``fab`` to run it: how connections are
really made, and how disconnections occur.

Connections
===========

We've documented how Fabric really connects to its hosts before, but it's
currently somewhat buried in the middle of the overall :doc:`execution docs
</usage/execution>`. Specifically, you'll want to skip over to the 
:ref:`connections` section and read it real quick. (You should really give that
entire document a once-over, but it's not absolutely required.)

As that section mentions, the key is simply that `~fabric.operations.run`,
`~fabric.operations.sudo` and the other operations only look in one place when
connecting: :ref:`env.host_string <host_string>`. All of the other mechanisms
for setting hosts are interpreted by the ``fab`` tool when it runs, and don't
matter when running as a library.

This is a good thing, insofar as it gives library users very granular control
over which commands are run on which hosts. However, at present, it also means
you may need to do a bit more heavy lifting compared to a regular fabfile: you
can't rely on :ref:`env.hosts <hosts>` or the host/role decorators, and instead
need to write your own ``for`` loops.

For example, this is how a fabfile could force a given subroutine (task) to run
on two hosts in a row::

    @hosts('a', 'b')
    def mytask():
        run('ls')

To get the same behavior in library usage, you'd need to do this::

    def mytask():
        run('ls')

    for host in ['a', 'b']:
        with settings(host_string=host):
            mytask()

In future revisions we'll be adding more tools to make this a bit easier,
perhaps something like ``execute(task_object, host_list)``, but for now it's up
to you.


Disconnecting
=============

The other main thing that ``fab`` does for you is to disconnect from all hosts
at the end of a session; otherwise, Python will sit around forever waiting for
those network resources to be released.

Fabric 0.9.4 and newer have a function you can use to do this easily:
`~fabric.network.disconnect_all`. Simply make sure your code calls this when it
terminates (typically in the ``finally`` clause of an outer ``try: finally``
statement -- lest errors in your code prevent disconnections from happening!)
and things ought to work pretty well.

If you're on Fabric 0.9.3 or older, you can simply do this (``disconnect_all``
just adds a bit of nice output to this logic)::

    from fabric.state import connections

    for key in connections.keys():
        connections[key].close()
        del connections[key]


Final note
==========

This document is a first draft, and may not cover absolutely every difference
between ``fab`` use and library use. However, the above should highlight the
largest stumbling blocks. When in doubt, note that in the Fabric source code,
``fabric/main.py`` contains the bulk of the extra work done by ``fab``, and may
serve as a useful reference.
