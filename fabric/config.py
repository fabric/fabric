from StringIO import StringIO

from invoke.config import Config as InvokeConfig, merge_dicts
from paramiko.config import SSHConfig

from .util import get_local_user


class Config(InvokeConfig):
    """
    An `invoke.config.Config` subclass with extra Fabric-related behavior.

    This class behaves like `invoke.config.Config` in every way, with the
    following exceptions:

    - its `global_defaults` staticmethod has been extended to add/modify some
      default settings (see its documentation, below, for details);
    - it accepts additional instantiation arguments related to loading
      ``ssh_config`` files.

    Intended for use with `.Connection`, as using vanilla
    `invoke.config.Config` objects would require users to manually define
    ``port``, ``user`` and so forth.

    .. seealso:: :doc:`/concepts/configuration`, :ref:`ssh-config`
    """
    def __init__(self, *args, **kwargs):
        """
        Creates a new Fabric-specific config object.

        For most API details, see `invoke.config.Config.__init__`. Parameters
        new to this subclass are listed below.

        :param ssh_config:
            Custom/explicit `paramiko.config.SSHConfig` object. If given,
            prevents loading of any SSH config files. Default: ``None``.
        """
        # Tease out our own kwargs.
        # TODO: consider moving more stuff out of __init__ and into methods so
        # there's less of this sort of thing? Eh.
        ssh_config = kwargs.pop('ssh_config', None)
        system_ssh_path = kwargs.pop('system_ssh_path', None)
        user_ssh_path = kwargs.pop('user_ssh_path', None)

        # TODO:
        # - _system_ssh_path (& param, defaults /etc/ssh/ssh_config)
        #   - make clear it's a full path not a prefix or dir
        # - _user_ssh_path (& param, defaults $HOME/.ssh/config)
        # - ssh_config param (defaults None)
        # - ssh_config_path param (defaults None)
        # - load_ssh_files() method, and called after super()
        # - set base_ssh_config attr

        super(Config, self).__init__(*args, **kwargs)

        #: A `paramiko.config.SSHConfig` object based on loaded config files
        #: and/or a manually supplied ``SSHConfig`` object.
        if ssh_config is None:
            ssh_config = SSHConfig()
            # TODO: Paramiko's API should get cleaned up a bit so we don't have
            # to do dumb stuff like this.
            ssh_config.parse(StringIO())
        self.base_ssh_config = ssh_config or SSHConfig()

    @staticmethod
    def global_defaults():
        """
        Default configuration values and behavior toggles.

        Fabric only extends this method in order to make minor adjustments and
        additions to Invoke's `~invoke.config.Config.global_defaults`; see its
        documentation for the base values, such as the config subtrees
        controlling behavior of ``run`` or how ``tasks`` behave.

        For Fabric-specific modifications and additions to the Invoke-level
        defaults, see our own config docs at :ref:`default-values`.
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
