from .configuration import Configuration


# TODO: inherit from, or proxy to, invoke.context.Context
class Connection(object):
    """
    A connection to an SSH daemon, with methods for commands and file transfer.
    """
    # TODO: attribute listings: manual in docstring, or can autodoc do it?

    def __init__(self, host, user=None, port=None, config=None):
        """
        Set up a new object representing a server connection.

        :param str host:
            the hostname (or IP address) of this connection. May include
            shorthand for the ``user`` and/or ``port`` parameters, of the form
            ``[user@]host[:port]``.

        :param str user:
            the login user for the remote connection. Defaults to your local
            login username.

        :param int port:
            the remote port. Defaults to ``22``.

        :param Configuration config:
            a `.Configuration` object to use when checking configuration
            values. If not given, uses a generic default configuration.

        :raises ValueError:
            if user or port values are given via both ``host`` shorthand *and*
            their own arguments. (We `refuse the temptation to guess
            <http://legacy.python.org/dev/peps/pep-0020/>`_.)
        """
        self.config = config or Configuration()
        self.user = user or self.config['local_user']
        self.port = port or self.config['default_port']

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
