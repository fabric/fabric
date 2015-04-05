from invoke.config import Config as InvokeConfig, merge_dicts

from .utils import get_local_user


class Config(InvokeConfig):
    """
    `invoke.config.Config` subclass with extra Fabric-related global defaults.

    This class behaves like `invoke.config.Config` in every way, save for that
    its `global_defaults` staticmethod has been extended to add Fabric-specific
    settings such as user and port number.

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


# TODO: inherit from, or proxy to, invoke.context.Context
class Connection(object):
    """
    A connection to an SSH daemon, with methods for commands and file transfer.

    This class inherits from Invoke's `.Context`, as it is a context within
    which commands, tasks etc can operate. It also encapsulates a Paramiko
    `.Client` instance, performing useful high level operations with that
    `.Client` and `.Channel` instances generated from it.

    Like `.Client`, `.Connection` has a basic "`create <__init__>`,
    `connect/open <open>`, `do work <run>`, `disconnect/close <close>`"
    lifecycle, though this is handled transparently: most users simply need to
    instantiate and call the interesting methods like `run` and `put`.
    """
    # TODO: push some of this into paramiko.client.Client? e.g. expand what
    # Client.exec_command does, it already allows configuring a subset of what
    # we do / will eventually do / did in 1.x.
    # It's silly to have to do .get_transport().open_session().
    def __init__(self, host, user=None, port=None, config=None):
        """
        Set up a new object representing a server connection.

        :param str host:
            the hostname (or IP address) of this connection. May include
            shorthand for the ``user`` and/or ``port`` parameters, of the form
            ``[user@]host[:port]``.

        :param str user:
            the login user for the remote connection. Defaults to
            ``config.user``.

        :param int port:
            the remote port. Defaults to ``config.port``.

        :param fabric.connection.Config config:
            configuration settings to use when executing methods on this
            `.Connection` (e.g. default SSH port and so forth).

            Default is an anonymous `.Config` object.

        :raises ValueError:
            if user or port values are given via both ``host`` shorthand *and*
            their own arguments. (We `refuse the temptation to guess`_).

        .. _refuse the temptation to guess:
            http://zen-of-python.info/
            in-the-face-of-ambiguity-refuse-the-temptation-to-guess.html#12
        """
        # TODO: how does this config mesh with the one from us being an Invoke
        # context, for keys not part of the defaults? Do we namespace all our
        # stuff or just overlay it? Starting with overlay, but...
        # TODO: also needs to be easier to obtain the defaults w/ only a subset
        # of things replaced; e.g. see our tests where we have to put in stupid
        # dummy values for 'user' when testing that replacing 'port' works OK.
        # Either needs to be extra Config 'levels' (bluh) or we explicitly
        # perform dict_merge() type stuff against user-supplied Config
        # instances (instead of bitching about what is missing).

        #: The .Config object referenced when handling default values (for e.g.
        #: user or port, when not explicitly given) or deciding how to behave.
        self.config = config if config is not None else Config()
        # TODO: when/how to run load_files, merge, load_shell_env, etc?
        # TODO: i.e. what is the lib use case here (and honestly in invoke too)?

        #: The username this connection will use to connect to the remote end.
        self.user = user or self.config.user
        #: The network port to connect on.
        self.port = port or self.config.port

        #: Whether or not this connection is actually open or not.
        self.is_connected = False


    def run(self, command):
        """
        Execute a shell command on the remote end of this connection.

        :param str command:
            The command to execute. Standard SSH daemons execute these
            commands within the connecting user's login shell, so shell
            semantics (pipes, redirects etc) may be used freely.

        :returns:
            A `~invoke.runner.Result` object containing the command's exit
            status, stdout/err, etc.
        """
        pass
