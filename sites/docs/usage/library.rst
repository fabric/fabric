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

That said, most use cases where you want to marry a given task ``X`` and a given list of hosts ``Y`` can, as of Fabric 1.3, be handled with the `~fabric.tasks.execute` function via ``execute(X, hosts=Y)``. Please see `~fabric.tasks.execute`'s documentation for details -- manual host string manipulation should be rarely necessary.

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

This document is an early draft, and may not cover absolutely every difference
between ``fab`` use and library use. However, the above should highlight the
largest stumbling blocks. When in doubt, note that in the Fabric source code,
``fabric/main.py`` contains the bulk of the extra work done by ``fab``, and may
serve as a useful reference.
