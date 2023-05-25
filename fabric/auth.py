from functools import partial
from getpass import getpass
from pathlib import Path

from paramiko import Agent, PKey
from paramiko.auth_strategy import (
    AuthStrategy,
    Password,
    InMemoryPrivateKey,
    OnDiskPrivateKey,
)

from .util import win32


class OpenSSHAuthStrategy(AuthStrategy):
    """
    Auth strategy that tries very hard to act like the OpenSSH client.

    .. warning::
        As of version 3.1, this class is **EXPERIMENTAL** and **incomplete**.
        It works best with passphraseless (eg ssh-agent) private key auth for
        now and will grow more features in future releases.

    For example, it accepts a `~paramiko.config.SSHConfig` and uses any
    relevant ``IdentityFile`` directives from that object, along with keys from
    your home directory and any local SSH agent. Keys specified at runtime are
    tried last, just as with ``ssh -i /path/to/key`` (this is one departure
    from the legacy/off-spec auth behavior observed in older Paramiko and
    Fabric versions).

    We explicitly do not document the full details here, because the point is
    to match the documented/observed behavior of OpenSSH. Please see the `ssh
    <https://man.openbsd.org/ssh>`_ and `ssh_config
    <https://man.openbsd.org/ssh_config>`_ man pages for more information.

    .. versionadded:: 3.1
    """

    # Skimming openssh code (ssh.c and sshconnect2.c) gives us the following
    # behavior to crib from:
    # - parse cli (initializing identity_files if any given)
    # - parse user config, then system config _unless_ user gave cli config
    # path; this will also add to identity_files if any IdentityFile found
    # (after the CLI ones)
    # - lots of value init, string interpolation, etc
    # - if no other identity_files exist at this point, fill in the ~/.ssh/
    # defaults:
    #   - in order: rsa, dsa, ecdsa, ecdsa_sk, ed25519, xmss (???)
    # - initial connection (ssh_connect() - presumably handshake/hostkey/kex)
    # - load all identity_files (and any implicit certs of those)
    # - eventually runs pubkey_prepare() which, per its own comment,
    # loads/assembles key material in this order:
    #   - certs - config file, then cli, skipping any non-user (?) certs
    #   - agent keys that are also listed in the config file
    #   - agent keys _not_ listed in config files
    #   - non-agent config file keys (this seems like it includes cli and
    #   implicit defaults)
    #   - once list is assembled, drop anything not listed in configured pubkey
    #   algorithms list
    # - auth_none to get list of acceptable authmethods
    # - while-loops along that, or next returned, list of acceptable
    # authmethods, using a handler table, so eg a 'standard' openssh on both
    # ends might start with 'publickey,password,keyboard-interactive'; so it'll
    # try all pubkeys found above before eventually trying a password prompt,
    # and then if THAT fails, it will try kbdint call-and-response (similar to
    # password but where server sends you the prompt(s) it wants displayed)

    def __init__(self, ssh_config, fabric_config, username):
        """
        Extends superclass with additional inputs.

        Specifically:

        - ``fabric_config``, a `fabric.Config` instance for the current
          session.
        - ``username``, which is unified by our intended caller so we don't
          have to - it's a synthesis of CLI, runtime,
          invoke/fabric-configuration, and ssh_config configuration.

        Also handles connecting to an SSH agent, if possible, for easier
        lifecycle tracking.
        """
        super().__init__(ssh_config=ssh_config)
        self.username = username
        self.config = fabric_config
        # NOTE: Agent seems designed to always 'work' even w/o a live agent, in
        # which case it just yields an empty key list.
        self.agent = Agent()

    def get_pubkeys(self):
        # Similar to OpenSSH, we first obtain sources in arbitrary order,
        # tracking where they came from and whether they were a cert.
        config_certs, config_keys, cli_certs, cli_keys = [], [], [], []
        # Our own configuration is treated like `ssh -i`, partly because that's
        # where our -i flag ends up, partly because our config data has no
        # direct OpenSSH analogue (it's _not_ in your ssh_config! it's
        # elsewhere!)
        for path in self.config.authentication.identities:
            try:
                key = PKey.from_path(path)
            except FileNotFoundError:
                continue
            source = OnDiskPrivateKey(
                username=self.username,
                source="python-config",
                path=path,
                pkey=key,
            )
            (cli_certs if key.public_blob else cli_keys).append(source)
        # Now load ssh_config IdentityFile directives, sorting again into
        # cert/key split.
        # NOTE: Config's ssh_config loader already behaves OpenSSH-compatibly:
        # if the user supplied a custom ssh_config file path, that is the only
        # one loaded; otherwise, it loads and merges the user and system paths.
        # TODO: CertificateFile support? Most people seem to rely on the
        # implicit cert loading of IdentityFile...
        for path in self.ssh_config.get("identityfile", []):
            try:
                key = PKey.from_path(path)
            except FileNotFoundError:
                continue
            source = OnDiskPrivateKey(
                username=self.username,
                source="ssh-config",
                path=path,
                pkey=key,
            )
            (config_certs if key.public_blob else config_keys).append(source)
        # At this point, if we've still got no keys or certs, look in the
        # default user locations.
        if not any((config_certs, config_keys, cli_certs, cli_keys)):
            user_ssh = Path.home() / f"{'' if win32 else '.'}ssh"
            # This is the same order OpenSSH documents as using.
            for type_ in ("rsa", "ecdsa", "ed25519", "dsa"):
                path = user_ssh / f"id_{type_}"
                try:
                    key = PKey.from_path(path)
                except FileNotFoundError:
                    continue
                source = OnDiskPrivateKey(
                    username=self.username,
                    source="implicit-home",
                    path=path,
                    pkey=key,
                )
                dest = config_certs if key.public_blob else config_keys
                dest.append(source)
        # TODO: set agent_keys to empty list if IdentitiesOnly is true
        agent_keys = self.agent.get_keys()

        # We've finally loaded everything; now it's time to throw them upwards
        # in the intended order...
        # TODO: define subroutine that dedupes (& honors
        # PubkeyAcceptedAlgorithms) then rub that on all of the below.
        # First, all local _certs_ (config wins over cli, for w/e reason)
        for source in config_certs:
            yield source
        for source in cli_certs:
            yield source
        # Then all agent keys, first ones that were also mentioned in configs,
        # then 'new' ones not found in configs.
        deferred_agent_keys = []
        for key in agent_keys:
            config_index = None
            for i, config_key in enumerate(config_keys):
                if config_key.pkey == key:
                    config_index = i
                    break
            if config_index:
                yield InMemoryPrivateKey(username=self.username, pkey=key)
                # Nuke so it doesn't get re-yielded by regular conf keys bit
                del config_keys[config_index]
            else:
                deferred_agent_keys.append(key)
        for key in deferred_agent_keys:
            yield InMemoryPrivateKey(username=self.username, pkey=key)
        for source in cli_keys:
            yield source
        # This will now be just the config-borne keys that were NOT in agent
        for source in config_keys:
            yield source

    def get_sources(self):
        # TODO: initial none-auth + tracking the response's allowed types.
        # however, SSHClient never did this deeply, and there's no guarantee a
        # server _will_ send anything but "any" anyways...
        # Public keys of all kinds typically first.
        yield from self.get_pubkeys()
        user = self.username
        prompter = partial(getpass, f"{user}'s password: ")
        # Then password.
        yield Password(username=self.username, password_getter=prompter)

    def authenticate(self, *args, **kwargs):
        # Just do what our parent would, except make sure we close() after.
        try:
            return super().authenticate(*args, **kwargs)
        finally:
            self.close()

    def close(self):
        """
        Shut down any resources we ourselves opened up.
        """
        # TODO: bare try/except here as "best effort"? ugh
        self.agent.close()
