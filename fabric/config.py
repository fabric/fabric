from invoke.config import Config as InvokeConfig, merge_dicts

from .util import get_local_user


class Config(InvokeConfig):
    """
    An `invoke.config.Config` subclass with extra Fabric-related defaults.

    This class behaves like `invoke.config.Config` in every way, except that
    its `global_defaults` staticmethod has been extended to add/modify some
    default settings. (See its documentation, below, for details.)

    Intended for use with `.Connection`, as using vanilla
    `invoke.config.Config` objects would require you to manually define
    ``port``, ``user`` and so forth.
    """
    @staticmethod
    def global_defaults():
        """
        Default configuration values and behavior toggles.

        Fabric only extends this method in order to make minor adjustments and
        additions to Invoke's `~invoke.config.Config.global_defaults`; see its
        documentation for the base values, such as the config subtrees
        controlling behavior of ``run`` or how ``tasks`` behave.

        Values that differ from Invoke's defaults:

        - ``run.replace_env``: ``True``, instead of ``False``. This is for
          security purposes (leaking local environment data remotely by default
          would be unsanitary) & for compatibility with the behavior of
          OpenSSH. (See also: the warning under
          `paramiko.channel.Channel.set_environment_variable`.)

        New-to-Fabric default values:

        * ``port``: TCP port number to which `.Connection` objects connect when
          not otherwise specified. Default: ``22``.
        * ``user``: Username given to the remote ``sshd`` when connecting.
          Default: your local username.
        """
        # TODO: is it worth moving all of our 'new' settings to a discrete
        # namespace for cleanliness' sake? e.g. ssh.port, ssh.user etc.
        # It wouldn't actually simplify this code any, but it would make it
        # easier for users to determine what came from which library/repo.
        defaults = InvokeConfig.global_defaults()
        ours = {
            'port': 22,
            'user': get_local_user(),
            'forward_agent': False,
            'run': {
                'replace_env': True,
            },
        }
        merge_dicts(defaults, ours)
        return defaults
