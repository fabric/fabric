from invoke import Context
from invoke.config import Config as InvokeConfig, merge_dicts
from paramiko.client import SSHClient, AutoAddPolicy

from .runners import Remote
from .transfer import Transfer
from .util import get_local_user


class Config(InvokeConfig):
    """
    An `invoke.config.Config` subclass with extra Fabric-related defaults.

    This class behaves like `invoke.config.Config` in every way, save for that
    its `~invoke.config.Config.global_defaults` staticmethod has been extended
    to add Fabric-specific settings such as user and port number.

    Intended for use with `.Connection`, as using vanilla
    `invoke.config.Config` objects would require you to manually define
    ``port``, ``user`` and so forth .
    """
    # NOTE: docs for these are kept in sites/docs/api/connection.rst for
    # tighter control over value display (avoids baking docs-building user's
    # username into the docs).
    @staticmethod
    def global_defaults():
        defaults = InvokeConfig.global_defaults()
        ours = {
            'port': 22,
            'user': get_local_user(),
        }
        merge_dicts(defaults, ours)
        return defaults


class Connection(Context):
    """
    A connection to an SSH daemon, with methods for commands and file transfer.

    This class inherits from Invoke's `~invoke.context.Context`, as it is a
    context within which commands, tasks etc can operate. It also encapsulates
    a Paramiko `~paramiko.client.SSHClient` instance, performing useful high
    level operations with that `~paramiko.client.SSHClient` and
    `~paramiko.channel.Channel` instances generated from it.

    Like `~paramiko.client.SSHClient`, `.Connection` has a basic "`create
    <__init__>`, `connect/open <open>`, `do work <run>`, `disconnect/close
    <close>`" lifecycle, though this is handled transparently: most users
    simply need to instantiate and call the interesting methods like `run` and
    `put`.

    .. note::
        This class rebinds `invoke.context.Context.run` to `.local` so both
        remote and local command execution can coexist.
    """
    # TODO: push some of this into paramiko.client.Client? e.g. expand what
    # Client.exec_command does, it already allows configuring a subset of what
    # we do / will eventually do / did in 1.x.
    # It's silly to have to do .get_transport().open_session().
    def __init__(self, host, user=None, port=None, config=None):
        """
        Set up a new object representing a server connection.

        :param str host:
            the hostname (or IP address) of this connection.

            May include shorthand for the ``user`` and/or ``port`` parameters,
            of the form ``user@host``, ``host:port``, or ``user@host:port``.

            .. note::
                Due to ambiguity, IPv6 host addresses are incompatible with the
                ``host:port`` shorthand (though ``user@host`` will still work
                OK). In other words, the presence of >1 ``:`` character will
                prevent any attempt to derive a shorthand port number; use the
                explicit ``port`` parameter instead.

        :param str user:
            the login user for the remote connection. Defaults to
            ``config.user``.

        :param int port:
            the remote port. Defaults to ``config.port``.

        :param fabric.connection.Config config:
            configuration settings to use when executing methods on this
            `.Connection` (e.g. default SSH port and so forth).

            Default is an anonymous `.Config` object.

        :raises exceptions.ValueError:
            if user or port values are given via both ``host`` shorthand *and*
            their own arguments. (We `refuse the temptation to guess`_).

        .. _refuse the temptation to guess:
            http://zen-of-python.info/
            in-the-face-of-ambiguity-refuse-the-temptation-to-guess.html#12
        """
        # NOTE: for now, we don't call our parent __init__, since all it does
        # is set a default config (to Invoke's Config, not ours). If
        # invoke.Context grows more behavior later we may need to change this.

        # TODO: how does this config mesh with the one from us being an Invoke
        # context, for keys not part of the defaults? Do we namespace all our
        # stuff or just overlay it? Starting with overlay, but...

        #: The .Config object referenced when handling default values (for e.g.
        #: user or port, when not explicitly given) or deciding how to behave.
        self.config = config if config is not None else Config()
        # TODO: when/how to run load_files, merge, load_shell_env, etc?
        # TODO: i.e. what is the lib use case here (and honestly in invoke too)

        shorthand = self.derive_shorthand(host)
        host = shorthand['host']
        err = "You supplied the {0} via both shorthand and kwarg! Please pick one." # noqa
        if shorthand['user'] is not None:
            if user is not None:
                raise ValueError(err.format('user'))
            user = shorthand['user']
        if shorthand['port'] is not None:
            if port is not None:
                raise ValueError(err.format('port'))
            port = shorthand['port']

        #: The hostname of the target server.
        self.host = host
        #: The username this connection will use to connect to the remote end.
        self.user = user or self.config.user
        #: The network port to connect on.
        self.port = port or self.config.port

        #: The `paramiko.client.SSHClient` instance this connection wraps.
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        self.client = client

        #: A convenience handle onto the return value of
        #: ``self.client.get_transport()``.
        self.transport = None

    def __str__(self):
        s = "<Connection id={0} user='{1.user}' host='{1.host}' port={1.port}>"
        return s.format(id(self), self)

    def derive_shorthand(self, host_string):
        user_hostport = host_string.rsplit('@', 1)
        hostport = user_hostport.pop()
        user = user_hostport[0] if user_hostport and user_hostport[0] else None

        # IPv6: can't reliably tell where addr ends and port begins, so don't
        # try (and don't bother adding special syntax either, user should avoid
        # this situation by using port=).
        if hostport.count(':') > 1:
            host = hostport
            port = None
        # IPv4: can split on ':' reliably.
        else:
            host_port = hostport.rsplit(':', 1)
            host = host_port.pop(0) or None
            port = host_port[0] if host_port and host_port[0] else None

        if port is not None:
            port = int(port)

        return {'user': user, 'host': host, 'port': port}

    @property
    def host_string(self):
        # TODO: remove this ASAP once a better way of representing connections
        # in aggregate results is found!
        return "{0}@{1}:{2}".format(self.user, self.host, self.port)

    @property
    def is_connected(self):
        """
        Whether or not this connection is actually open.
        """
        return self.transport.active if self.transport else False

    def open(self):
        """
        Initiate an SSH connection to the host/port this object is bound to.

        Also saves a handle to the now-set Transport object for easier access.
        """
        if not self.is_connected:
            self.client.connect(hostname=self.host, port=self.port)
            self.transport = self.client.get_transport()

    def close(self):
        """
        Terminate the network connection to the remote end, if open.

        If no connection is open, this method does nothing.
        """
        if self.is_connected:
            self.client.close()

    def _create_session(self):
        # TODO: make this a contextmanager perhaps? 'with cxn.session() as
        # channel: channel.exec_command(blah)' - tho still unsure if it should
        # be public API right away.
        # TODO: implies we may want to do the same for Connection itself
        # (though that might not be the primary API for it)
        self.open()
        return self.transport.open_session()

    def run(self, command, **kwargs):
        """
        Execute a shell command on the remote end of this connection.

        This method wraps an SSH-capable implementation of
        `invoke.runners.Runner.run`; see its docs for details.
        """
        self.open()
        return Remote(context=self).run(command, **kwargs)

    def local(self, *args, **kwargs):
        """
        Execute a shell command on the local system.

        This method is a straight wrapper of `invoke.run`; see its docs for
        details and call signature.
        """
        return super(Connection, self).run(*args, **kwargs)

    def sftp(self):
        """
        Return a `~paramiko.sftp_client.SFTPClient` object.

        If called more than one time, memoizes the first result; thus, any
        given `.Connection` instance will only ever have a single SFTP client,
        and state (such as that managed by
        `~paramiko.sftp_client.SFTPClient.chdir`) will be preserved.
        """
        self.open()
        if not hasattr(self, '_sftp'):
            self._sftp = self.client.open_sftp()
        return self._sftp

    def get(self, *args, **kwargs):
        """
        Get a remote file to the local filesystem or file-like object.

        Simply a wrapper for `.Transfer.get`. Please see its documentation for
        all details.
        """
        return Transfer(self).get(*args, **kwargs)

    def put(self, *args, **kwargs):
        """
        Put a remote file (or file-like object) to the remote filesystem.

        Simply a wrapper for `.Transfer.put`. Please see its documentation for
        all details.
        """
        return Transfer(self).put(*args, **kwargs)


class Group(list):
    """
    A collection of `.Connection` objects whose API operates on its contents.
    """
    def __init__(self, hosts=None):
        """
        Create a group of connections from an iterable of shorthand strings.

        See `.Connection` for details on the format of these strings - they
        will be used as the first positional argument of `.Connection`
        constructors.
        """
        # TODO: allow splat-args form in addition to iterable arg?
        if hosts:
            self.extend(map(Connection, hosts))

    @classmethod
    def from_connections(cls, connections):
        """
        Alternate constructor accepting `.Connection` objects.
        """
        group = cls()
        group.extend(connections)
        return group

    def run(self, *args, **kwargs):
        # TODO: how to change method of execution across contents? subclass,
        # kwargs, additional methods, inject an executor?
        # TODO: retval needs to be host objects or something non-string. See
        # how tutorial mentions 'ResultSet' - useful to construct or no?
        # TODO: also need way to deal with duplicate connections (see THOUGHTS)
        result = {}
        for cxn in self:
            result[cxn.host_string] = cxn.run(*args, **kwargs)
        return result

    # TODO: execute() as mentioned in tutorial
