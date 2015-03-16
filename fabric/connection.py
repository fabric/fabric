from invoke.config import Config, merge_dicts

from .utils import get_local_user


# NOTE: docs for this member are kept in sites/docs/api/connection.rst for
# tighter control over value display (avoids baking docs-building user's
# username into the docs).
default_config = Config({
    'port': 22,
    # TODO: make this default to None and fill in later, so it doesn't appear
    # in the docs as <whoever built the docs>? Or just modify it after
    # declaration, heh?
    'user': get_local_user(),
})



# TODO: inherit from, or proxy to, invoke.context.Context
class Connection(object):
    """
    A connection to an SSH daemon, with methods for commands and file transfer.
    """
    # TODO: attribute comments

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
            the configuration settings to use when executing methods on this
            `.Connection` (e.g. default SSH port and so forth). Defaults to
            `.default_config`.

        :raises ValueError:
            if user or port values are given via both ``host`` shorthand *and*
            their own arguments. (We `refuse the temptation to guess`_).

        .. _refuse the temptation to guess:
            http://zen-of-python.info/
            in-the-face-of-ambiguity-refuse-the-temptation-to-guess.html#12
        """
        # TODO: how does this config mesh with the one from us being an Invoke
        # context? Do we namespace all our stuff or just overlay it? Do we
        # merge our settings into .defaults / .overrides?
        self.config = default_config.clone() if config is None else config
        # TODO: when/how to run load_files, merge, load_shell_env, etc?
        # TODO: i.e. what is the lib use case here (and honestly in invoke too)?
        self.user = user or self.config.local_user
        self.port = port or self.config.default_port

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
