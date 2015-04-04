import invoke

from .utils import get_local_user


# NOTE: docs for this member are kept in sites/docs/api/connection.rst for
# tighter control over value display (avoids baking docs-building user's
# username into the docs).
global_defaults = {
    'port': 22,
    'user': get_local_user(),
}


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

        :param invoke.config.Config config:
            configuration settings to use when executing methods on this
            `.Connection` (e.g. default SSH port and so forth).

            Default is an anonymous `.Config` object whose ``defaults`` level
            is `invoke.config.global_defaults` and whose ``overrides`` level is
            `fabric.connection.global_defaults`.

            .. note::
                If you provide your own `.Config` instance, it **must** contain
                values for the keys found in the abovementioned
                ``global_defaults`` data structures.

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
        if config is None:
            config = invoke.config.Config(
                defaults=invoke.config.global_defaults,
                overrides=global_defaults
            )
        self.config = config
        # TODO: when/how to run load_files, merge, load_shell_env, etc?
        # TODO: i.e. what is the lib use case here (and honestly in invoke too)?
        self.user = user or self.config.user
        self.port = port or self.config.port

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
