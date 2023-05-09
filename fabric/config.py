import copy
import errno
import os

from invoke.config import Config as InvokeConfig, merge_dicts
from paramiko.config import SSHConfig

from .runners import Remote, RemoteShell
from .util import get_local_user, debug


class Config(InvokeConfig):
    """
    An `invoke.config.Config` subclass with extra Fabric-related behavior.

    This class behaves like `invoke.config.Config` in every way, with the
    following exceptions:

    - its `global_defaults` staticmethod has been extended to add/modify some
      default settings (see its documentation, below, for details);
    - it triggers loading of Fabric-specific env vars (e.g.
      ``FABRIC_RUN_HIDE=true`` instead of ``INVOKE_RUN_HIDE=true``) and
      filenames (e.g. ``/etc/fabric.yaml`` instead of ``/etc/invoke.yaml``).
    - it extends the API to account for loading ``ssh_config`` files (which are
      stored as additional attributes and have no direct relation to the
      regular config data/hierarchy.)
    - it adds a new optional constructor, `from_v1`, which :ref:`generates
      configuration data from Fabric 1 <from-v1>`.

    Intended for use with `.Connection`, as using vanilla
    `invoke.config.Config` objects would require users to manually define
    ``port``, ``user`` and so forth.

    .. seealso:: :doc:`/concepts/configuration`, :ref:`ssh-config`

    .. versionadded:: 2.0
    """

    prefix = "fabric"

    @classmethod
    def from_v1(cls, env, **kwargs):
        """
        Alternate constructor which uses Fabric 1's ``env`` dict for settings.

        All keyword arguments besides ``env`` are passed unmolested into the
        primary constructor, with the exception of ``overrides``, which is used
        internally & will end up resembling the data from ``env`` with the
        user-supplied overrides on top.

        .. warning::
            Because your own config overrides will win over data from ``env``,
            make sure you only set values you *intend* to change from your v1
            environment!

        For details on exactly which ``env`` vars are imported and what they
        become in the new API, please see :ref:`v1-env-var-imports`.

        :param env:
            An explicit Fabric 1 ``env`` dict (technically, any
            ``fabric.utils._AttributeDict`` instance should work) to pull
            configuration from.

        .. versionadded:: 2.4
        """
        # TODO: automagic import, if we can find a way to test that
        # Use overrides level (and preserve whatever the user may have given)
        # TODO: we really do want arbitrary number of config levels, don't we?
        # TODO: most of these need more care re: only filling in when they
        # differ from the v1 default. As-is these won't overwrite runtime
        # overrides (due to .setdefault) but they may still be filling in empty
        # values to stomp on lower level config levels...
        data = kwargs.pop("overrides", {})
        # TODO: just use a dataproxy or defaultdict??
        for subdict in ("connect_kwargs", "run", "sudo", "timeouts"):
            data.setdefault(subdict, {})
        # PTY use
        data["run"].setdefault("pty", env.always_use_pty)
        # Gateway
        data.setdefault("gateway", env.gateway)
        # Agent forwarding
        data.setdefault("forward_agent", env.forward_agent)
        # Key filename(s)
        if env.key_filename is not None:
            data["connect_kwargs"].setdefault("key_filename", env.key_filename)
        # Load keys from agent?
        data["connect_kwargs"].setdefault("allow_agent", not env.no_agent)
        data.setdefault("ssh_config_path", env.ssh_config_path)
        # Sudo password
        data["sudo"].setdefault("password", env.sudo_password)
        # Vanilla password (may be used for regular and/or sudo, depending)
        passwd = env.password
        data["connect_kwargs"].setdefault("password", passwd)
        if not data["sudo"]["password"]:
            data["sudo"]["password"] = passwd
        data["sudo"].setdefault("prompt", env.sudo_prompt)
        data["timeouts"].setdefault("connect", env.timeout)
        data.setdefault("load_ssh_configs", env.use_ssh_config)
        data["run"].setdefault("warn", env.warn_only)
        # Put overrides back for real constructor and go
        kwargs["overrides"] = data
        return cls(**kwargs)

    def __init__(self, *args, **kwargs):
        """
        Creates a new Fabric-specific config object.

        For most API details, see `invoke.config.Config.__init__`. Parameters
        new to this subclass are listed below.

        :param ssh_config:
            Custom/explicit `paramiko.config.SSHConfig` object. If given,
            prevents loading of any SSH config files. Default: ``None``.

        :param str runtime_ssh_path:
            Runtime SSH config path to load. Prevents loading of system/user
            files if given. Default: ``None``.

        :param str system_ssh_path:
            Location of the system-level SSH config file. Default:
            ``/etc/ssh/ssh_config``.

        :param str user_ssh_path:
            Location of the user-level SSH config file. Default:
            ``~/.ssh/config``.

        :param bool lazy:
            Has the same meaning as the parent class' ``lazy``, but
            additionally controls whether SSH config file loading is deferred
            (requires manually calling `load_ssh_config` sometime.) For
            example, one may need to wait for user input before calling
            `set_runtime_ssh_path`, which will inform exactly what
            `load_ssh_config` does.
        """
        # Tease out our own kwargs.
        # TODO: consider moving more stuff out of __init__ and into methods so
        # there's less of this sort of splat-args + pop thing? Eh.
        ssh_config = kwargs.pop("ssh_config", None)
        lazy = kwargs.get("lazy", False)
        self.set_runtime_ssh_path(kwargs.pop("runtime_ssh_path", None))
        system_path = kwargs.pop("system_ssh_path", "/etc/ssh/ssh_config")
        self._set(_system_ssh_path=system_path)
        self._set(_user_ssh_path=kwargs.pop("user_ssh_path", "~/.ssh/config"))

        # Record whether we were given an explicit object (so other steps know
        # whether to bother loading from disk or not)
        # This needs doing before super __init__ as that calls our post_init
        explicit = ssh_config is not None
        self._set(_given_explicit_object=explicit)

        # Arrive at some non-None SSHConfig object (upon which to run .parse()
        # later, in _load_ssh_file())
        if ssh_config is None:
            ssh_config = SSHConfig()
        self._set(base_ssh_config=ssh_config)

        # Now that our own attributes have been prepared & kwargs yanked, we
        # can fall up into parent __init__()
        super().__init__(*args, **kwargs)

        # And finally perform convenience non-lazy bits if needed
        if not lazy:
            self.load_ssh_config()

    def set_runtime_ssh_path(self, path):
        """
        Configure a runtime-level SSH config file path.

        If set, this will cause `load_ssh_config` to skip system and user
        files, as OpenSSH does.

        .. versionadded:: 2.0
        """
        self._set(_runtime_ssh_path=path)

    def load_ssh_config(self):
        """
        Load SSH config file(s) from disk.

        Also (beforehand) ensures that Invoke-level config re: runtime SSH
        config file paths, is accounted for.

        .. versionadded:: 2.0
        """
        # Update the runtime SSH config path (assumes enough regular config
        # levels have been loaded that anyone wanting to transmit this info
        # from a 'vanilla' Invoke config, has gotten it set.)
        if self.ssh_config_path:
            self._runtime_ssh_path = self.ssh_config_path
        # Load files from disk if we weren't given an explicit SSHConfig in
        # __init__
        if not self._given_explicit_object:
            self._load_ssh_files()

    def clone(self, *args, **kwargs):
        # TODO: clone() at this point kinda-sorta feels like it's retreading
        # __reduce__ and the related (un)pickling stuff...
        # Get cloned obj.
        # NOTE: Because we also extend .init_kwargs, the actual core SSHConfig
        # data is passed in at init time (ensuring no files get loaded a 2nd,
        # etc time) and will already be present, so we don't need to set
        # .base_ssh_config ourselves. Similarly, there's no need to worry about
        # how the SSH config paths may be inaccurate until below; nothing will
        # be referencing them.
        new = super().clone(*args, **kwargs)
        # Copy over our custom attributes, so that the clone still resembles us
        # re: recording where the data originally came from (in case anything
        # re-runs ._load_ssh_files(), for example).
        for attr in (
            "_runtime_ssh_path",
            "_system_ssh_path",
            "_user_ssh_path",
        ):
            setattr(new, attr, getattr(self, attr))
        # Load SSH configs, in case they weren't prior to now (e.g. a vanilla
        # Invoke clone(into), instead of a us-to-us clone.)
        self.load_ssh_config()
        # All done
        return new

    def _clone_init_kwargs(self, *args, **kw):
        # Parent kwargs
        kwargs = super()._clone_init_kwargs(*args, **kw)
        # Transmit our internal SSHConfig via explicit-obj kwarg, thus
        # bypassing any file loading. (Our extension of clone() above copies
        # over other attributes as well so that the end result looks consistent
        # with reality.)
        new_config = SSHConfig()
        # TODO: as with other spots, this implies SSHConfig needs a cleaner
        # public API re: creating and updating its core data.
        new_config._config = copy.deepcopy(self.base_ssh_config._config)
        return dict(kwargs, ssh_config=new_config)

    def _load_ssh_files(self):
        """
        Trigger loading of configured SSH config file paths.

        Expects that ``base_ssh_config`` has already been set to an
        `~paramiko.config.SSHConfig` object.

        :returns: ``None``.
        """
        # TODO: does this want to more closely ape the behavior of
        # InvokeConfig.load_files? re: having a _found attribute for each that
        # determines whether to load or skip
        if self._runtime_ssh_path is not None:
            path = self._runtime_ssh_path
            # Manually blow up like open() (_load_ssh_file normally doesn't)
            if not os.path.exists(path):
                raise FileNotFoundError(
                    errno.ENOENT, "No such file or directory", path
                )
            self._load_ssh_file(os.path.expanduser(path))
        elif self.load_ssh_configs:
            for path in (self._user_ssh_path, self._system_ssh_path):
                self._load_ssh_file(os.path.expanduser(path))

    def _load_ssh_file(self, path):
        """
        Attempt to open and parse an SSH config file at ``path``.

        Does nothing if ``path`` is not a path to a valid file.

        :returns: ``None``.
        """
        if os.path.isfile(path):
            old_rules = len(self.base_ssh_config._config)
            with open(path) as fd:
                self.base_ssh_config.parse(fd)
            new_rules = len(self.base_ssh_config._config)
            msg = "Loaded {} new ssh_config rules from {!r}"
            debug(msg.format(new_rules - old_rules, path))
        else:
            debug("File not found, skipping")

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

        .. versionadded:: 2.0
        .. versionchanged:: 3.1
            Added the ``authentication`` settings section, plus sub-attributes
            such as ``authentication.strategy_class``.
        """
        # TODO: hrm should the run-related things actually be derived from the
        # runner_class? E.g. Local defines local stuff, Remote defines remote
        # stuff? Doesn't help with the final config tree tho...
        # TODO: as to that, this is a core problem, Fabric wants split
        # local/remote stuff, eg replace_env wants to be False for local and
        # True remotely; shell wants to differ depending on target (and either
        # way, does not want to use local interrogation for remote)
        # TODO: is it worth moving all of our 'new' settings to a discrete
        # namespace for cleanliness' sake? e.g. ssh.port, ssh.user etc.
        # It wouldn't actually simplify this code any, but it would make it
        # easier for users to determine what came from which library/repo.
        defaults = InvokeConfig.global_defaults()
        # TODO 4.0: this is already a mess, strongly consider a new 'ssh'
        # subtree because otherwise it's guessing where, or whether, 'ssh' is
        # in the setting name! i.e. 'inline_ssh_env' -> ssh.use_inline_env,
        # 'load_ssh_configs' -> ssh.load_configs, 'ssh_config_path' ->
        # ssh.config_path, etc
        ours = {
            "authentication": {
                "identities": [],
                "strategy_class": None,
            },
            "connect_kwargs": {},
            "forward_agent": False,
            "gateway": None,
            "inline_ssh_env": True,
            "load_ssh_configs": True,
            "port": 22,
            "runners": {"remote": Remote, "remote_shell": RemoteShell},
            "ssh_config_path": None,
            "tasks": {"collection_name": "fabfile"},
            # TODO: this becomes an override/extend once Invoke grows execution
            # timeouts (which should be timeouts.execute)
            "timeouts": {"connect": None},
            "user": get_local_user(),
        }
        merge_dicts(defaults, ours)
        return defaults
