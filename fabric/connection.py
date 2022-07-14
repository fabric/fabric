from contextlib import contextmanager
from threading import Event

try:
    from invoke.vendor.six import StringIO
    from invoke.vendor.decorator import decorator
    from invoke.vendor.six import string_types
except ImportError:
    from six import StringIO
    from decorator import decorator
    from six import string_types
import socket

from invoke import Context
from invoke.exceptions import ThreadException
from paramiko.agent import AgentRequestHandler
from paramiko.client import SSHClient, AutoAddPolicy
from paramiko.config import SSHConfig
from paramiko.proxy import ProxyCommand

from .config import Config
from .exceptions import InvalidV1Env
from .transfer import Transfer
from .tunnels import TunnelManager, Tunnel


@decorator
def opens(method, self, *args, **kwargs):
    self.open()
    return method(self, *args, **kwargs)


def derive_shorthand(host_string):
    user_hostport = host_string.rsplit("@", 1)
    hostport = user_hostport.pop()
    user = user_hostport[0] if user_hostport and user_hostport[0] else None

    # IPv6: can't reliably tell where addr ends and port begins, so don't
    # try (and don't bother adding special syntax either, user should avoid
    # this situation by using port=).
    if hostport.count(":") > 1:
        host = hostport
        port = None
    # IPv4: can split on ':' reliably.
    else:
        host_port = hostport.rsplit(":", 1)
        host = host_port.pop(0) or None
        port = host_port[0] if host_port and host_port[0] else None

    if port is not None:
        port = int(port)

    return {"user": user, "host": host, "port": port}


class Connection(Context):
    """
    A connection to an SSH daemon, with methods for commands and file transfer.

    **Basics**

    This class inherits from Invoke's `~invoke.context.Context`, as it is a
    context within which commands, tasks etc can operate. It also encapsulates
    a Paramiko `~paramiko.client.SSHClient` instance, performing useful high
    level operations with that `~paramiko.client.SSHClient` and
    `~paramiko.channel.Channel` instances generated from it.

    .. _connect_kwargs:

    .. note::
        Many SSH specific options -- such as specifying private keys and
        passphrases, timeouts, disabling SSH agents, etc -- are handled
        directly by Paramiko and should be specified via the
        :ref:`connect_kwargs argument <connect_kwargs-arg>` of the constructor.

    **Lifecycle**

    `.Connection` has a basic "`create <__init__>`, `connect/open <open>`, `do
    work <run>`, `disconnect/close <close>`" lifecycle:

    - `Instantiation <__init__>` imprints the object with its connection
      parameters (but does **not** actually initiate the network connection).

        - An alternate constructor exists for users :ref:`upgrading piecemeal
          from Fabric 1 <from-v1>`: `from_v1`

    - Methods like `run`, `get` etc automatically trigger a call to
      `open` if the connection is not active; users may of course call `open`
      manually if desired.
    - It's best to explicitly close your connections when done using them. This
      can be accomplished by manually calling `close`, or by using the object
      as a contextmanager::

          with Connection('host') as c:
             c.run('command')
             c.put('file')

      .. warning::
          While Fabric (and Paramiko) attempt to register connections for
          automatic garbage collection, it's not currently safe to rely on that
          feature, as it can lead to end-of-process hangs and similar behavior.

    .. note::
        This class rebinds `invoke.context.Context.run` to `.local` so both
        remote and local command execution can coexist.

    **Configuration**

    Most `.Connection` parameters honor :doc:`Invoke-style configuration
    </concepts/configuration>` as well as any applicable :ref:`SSH config file
    directives <connection-ssh-config>`. For example, to end up with a
    connection to ``admin@myhost``, one could:

    - Use any built-in config mechanism, such as ``/etc/fabric.yml``,
      ``~/.fabric.json``, collection-driven configuration, env vars, etc,
      stating ``user: admin`` (or ``{"user": "admin"}``, depending on config
      format.) Then ``Connection('myhost')`` would implicitly have a ``user``
      of ``admin``.
    - Use an SSH config file containing ``User admin`` within any applicable
      ``Host`` header (``Host myhost``, ``Host *``, etc.) Again,
      ``Connection('myhost')`` will default to an ``admin`` user.
    - Leverage host-parameter shorthand (described in `.Config.__init__`), i.e.
      ``Connection('admin@myhost')``.
    - Give the parameter directly: ``Connection('myhost', user='admin')``.

    The same applies to agent forwarding, gateways, and so forth.

    .. versionadded:: 2.0
    """

    # NOTE: these are initialized here to hint to invoke.Config.__setattr__
    # that they should be treated as real attributes instead of config proxies.
    # (Additionally, we're doing this instead of using invoke.Config._set() so
    # we can take advantage of Sphinx's attribute-doc-comment static analysis.)
    # Once an instance is created, these values will usually be non-None
    # because they default to the default config values.
    host = None
    original_host = None
    user = None
    port = None
    ssh_config = None
    gateway = None
    forward_agent = None
    connect_timeout = None
    connect_kwargs = None
    client = None
    transport = None
    _sftp = None
    _agent_handler = None

    @classmethod
    def from_v1(cls, env, **kwargs):
        """
        Alternate constructor which uses Fabric 1's ``env`` dict for settings.

        All keyword arguments besides ``env`` are passed unmolested into the
        primary constructor.

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
        # TODO: import fabric.state.env (need good way to test it first...)
        # TODO: how to handle somebody accidentally calling this in a process
        # where 'fabric' is fabric 2, and there's no fabric 1? Probably just a
        # re-raise of ImportError??
        # Our only requirement is a non-empty host_string
        if not env.host_string:
            raise InvalidV1Env(
                "Supplied v1 env has an empty `host_string` value! Please make sure you're calling Connection.from_v1 within a connected Fabric 1 session."  # noqa
            )
        # TODO: detect collisions with kwargs & except instead of overwriting?
        # (More Zen of Python compliant, but also, effort, and also, makes it
        # harder for users to intentionally overwrite!)
        connect_kwargs = kwargs.setdefault("connect_kwargs", {})
        kwargs.setdefault("host", env.host_string)
        shorthand = derive_shorthand(env.host_string)
        # TODO: don't we need to do the below skipping for user too?
        kwargs.setdefault("user", env.user)
        # Skip port if host string seemed to have it; otherwise we hit our own
        # ambiguity clause in __init__. v1 would also have been doing this
        # anyways (host string wins over other settings).
        if not shorthand["port"]:
            # Run port through int(); v1 inexplicably has a string default...
            kwargs.setdefault("port", int(env.port))
        # key_filename defaults to None in v1, but in v2, we expect it to be
        # either unset, or set to a list. Thus, we only pull it over if it is
        # not None.
        if env.key_filename is not None:
            connect_kwargs.setdefault("key_filename", env.key_filename)
        # Obtain config values, if not given, from its own from_v1
        # NOTE: not using setdefault as we truly only want to call
        # Config.from_v1 when necessary.
        if "config" not in kwargs:
            kwargs["config"] = Config.from_v1(env)
        return cls(**kwargs)

    # TODO: should "reopening" an existing Connection object that has been
    # closed, be allowed? (See e.g. how v1 detects closed/semi-closed
    # connections & nukes them before creating a new client to the same host.)
    # TODO: push some of this into paramiko.client.Client? e.g. expand what
    # Client.exec_command does, it already allows configuring a subset of what
    # we do / will eventually do / did in 1.x. It's silly to have to do
    # .get_transport().open_session().
    def __init__(
        self,
        host,
        user=None,
        port=None,
        config=None,
        gateway=None,
        forward_agent=None,
        connect_timeout=None,
        connect_kwargs=None,
        inline_ssh_env=None,
    ):
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

            .. note::
                If ``host`` matches a ``Host`` clause in loaded SSH config
                data, and that ``Host`` clause contains a ``Hostname``
                directive, the resulting `.Connection` object will behave as if
                ``host`` is equal to that ``Hostname`` value.

                In all cases, the original value of ``host`` is preserved as
                the ``original_host`` attribute.

                Thus, given SSH config like so::

                    Host myalias
                        Hostname realhostname

                a call like ``Connection(host='myalias')`` will result in an
                object whose ``host`` attribute is ``realhostname``, and whose
                ``original_host`` attribute is ``myalias``.

        :param str user:
            the login user for the remote connection. Defaults to
            ``config.user``.

        :param int port:
            the remote port. Defaults to ``config.port``.

        :param config:
            configuration settings to use when executing methods on this
            `.Connection` (e.g. default SSH port and so forth).

            Should be a `.Config` or an `invoke.config.Config`
            (which will be turned into a `.Config`).

            Default is an anonymous `.Config` object.

        :param gateway:
            An object to use as a proxy or gateway for this connection.

            This parameter accepts one of the following:

            - another `.Connection` (for a ``ProxyJump`` style gateway);
            - a shell command string (for a ``ProxyCommand`` style style
              gateway).

            Default: ``None``, meaning no gatewaying will occur (unless
            otherwise configured; if one wants to override a configured gateway
            at runtime, specify ``gateway=False``.)

            .. seealso:: :ref:`ssh-gateways`

        :param bool forward_agent:
            Whether to enable SSH agent forwarding.

            Default: ``config.forward_agent``.

        :param int connect_timeout:
            Connection timeout, in seconds.

            Default: ``config.timeouts.connect``.


        :param dict connect_kwargs:

            .. _connect_kwargs-arg:

            Keyword arguments handed verbatim to
            `SSHClient.connect <paramiko.client.SSHClient.connect>` (when
            `.open` is called).

            `.Connection` tries not to grow additional settings/kwargs of its
            own unless it is adding value of some kind; thus,
            ``connect_kwargs`` is currently the right place to hand in paramiko
            connection parameters such as ``pkey`` or ``key_filename``. For
            example::

                c = Connection(
                    host="hostname",
                    user="admin",
                    connect_kwargs={
                        "key_filename": "/home/myuser/.ssh/private.key",
                    },
                )

            Default: ``config.connect_kwargs``.

        :param bool inline_ssh_env:
            Whether to send environment variables "inline" as prefixes in front
            of command strings (``export VARNAME=value && mycommand here``),
            instead of trying to submit them through the SSH protocol itself
            (which is the default behavior). This is necessary if the remote
            server has a restricted ``AcceptEnv`` setting (which is the common
            default).

            The default value is the value of the ``inline_ssh_env``
            :ref:`configuration value <default-values>` (which itself defaults
            to ``False``).

            .. warning::
                This functionality does **not** currently perform any shell
                escaping on your behalf! Be careful when using nontrivial
                values, and note that you can put in your own quoting,
                backslashing etc if desired.

                Consider using a different approach (such as actual
                remote shell scripts) if you run into too many issues here.

            .. note::
                When serializing into prefixed ``FOO=bar`` format, we apply the
                builtin `sorted` function to the env dictionary's keys, to
                remove what would otherwise be ambiguous/arbitrary ordering.

            .. note::
                This setting has no bearing on *local* shell commands; it only
                affects remote commands, and thus, methods like `.run` and
                `.sudo`.

        :raises ValueError:
            if user or port values are given via both ``host`` shorthand *and*
            their own arguments. (We `refuse the temptation to guess`_).

        .. _refuse the temptation to guess:
            http://zen-of-python.info/
            in-the-face-of-ambiguity-refuse-the-temptation-to-guess.html#12

        .. versionchanged:: 2.3
            Added the ``inline_ssh_env`` parameter.
        """
        # NOTE: parent __init__ sets self._config; for now we simply overwrite
        # that below. If it's somehow problematic we would want to break parent
        # __init__ up in a manner that is more cleanly overrideable.
        super(Connection, self).__init__(config=config)

        #: The .Config object referenced when handling default values (for e.g.
        #: user or port, when not explicitly given) or deciding how to behave.
        if config is None:
            config = Config()
        # Handle 'vanilla' Invoke config objects, which need cloning 'into' one
        # of our own Configs (which grants the new defaults, etc, while not
        # squashing them if the Invoke-level config already accounted for them)
        elif not isinstance(config, Config):
            config = config.clone(into=Config)
        self._set(_config=config)
        # TODO: when/how to run load_files, merge, load_shell_env, etc?
        # TODO: i.e. what is the lib use case here (and honestly in invoke too)

        shorthand = self.derive_shorthand(host)
        host = shorthand["host"]
        err = "You supplied the {} via both shorthand and kwarg! Please pick one."  # noqa
        if shorthand["user"] is not None:
            if user is not None:
                raise ValueError(err.format("user"))
            user = shorthand["user"]
        if shorthand["port"] is not None:
            if port is not None:
                raise ValueError(err.format("port"))
            port = shorthand["port"]

        # NOTE: we load SSH config data as early as possible as it has
        # potential to affect nearly every other attribute.
        #: The per-host SSH config data, if any. (See :ref:`ssh-config`.)
        self.ssh_config = self.config.base_ssh_config.lookup(host)

        self.original_host = host
        #: The hostname of the target server.
        self.host = host
        if "hostname" in self.ssh_config:
            # TODO: log that this occurred?
            self.host = self.ssh_config["hostname"]

        #: The username this connection will use to connect to the remote end.
        self.user = user or self.ssh_config.get("user", self.config.user)
        # TODO: is it _ever_ possible to give an empty user value (e.g.
        # user='')? E.g. do some SSH server specs allow for that?

        #: The network port to connect on.
        self.port = port or int(self.ssh_config.get("port", self.config.port))

        # Gateway/proxy/bastion/jump setting: non-None values - string,
        # Connection, even eg False - get set directly; None triggers seek in
        # config/ssh_config
        #: The gateway `.Connection` or ``ProxyCommand`` string to be used,
        #: if any.
        self.gateway = gateway if gateway is not None else self.get_gateway()
        # NOTE: we use string above, vs ProxyCommand obj, to avoid spinning up
        # the ProxyCommand subprocess at init time, vs open() time.
        # TODO: make paramiko.proxy.ProxyCommand lazy instead?

        if forward_agent is None:
            # Default to config...
            forward_agent = self.config.forward_agent
            # But if ssh_config is present, it wins
            if "forwardagent" in self.ssh_config:
                # TODO: SSHConfig really, seriously needs some love here, god
                map_ = {"yes": True, "no": False}
                forward_agent = map_[self.ssh_config["forwardagent"]]
        #: Whether agent forwarding is enabled.
        self.forward_agent = forward_agent

        if connect_timeout is None:
            connect_timeout = self.ssh_config.get(
                "connecttimeout", self.config.timeouts.connect
            )
        if connect_timeout is not None:
            connect_timeout = int(connect_timeout)
        #: Connection timeout
        self.connect_timeout = connect_timeout

        #: Keyword arguments given to `paramiko.client.SSHClient.connect` when
        #: `open` is called.
        self.connect_kwargs = self.resolve_connect_kwargs(connect_kwargs)

        #: The `paramiko.client.SSHClient` instance this connection wraps.
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        self.client = client

        #: A convenience handle onto the return value of
        #: ``self.client.get_transport()``.
        self.transport = None

        if inline_ssh_env is None:
            inline_ssh_env = self.config.inline_ssh_env
        #: Whether to construct remote command lines with env vars prefixed
        #: inline.
        self.inline_ssh_env = inline_ssh_env

    def resolve_connect_kwargs(self, connect_kwargs):
        # TODO: is it better to pre-empt conflicts w/ manually-handled
        # connect() kwargs (hostname, username, etc) here or in open()? We're
        # doing open() for now in case e.g. someone manually modifies
        # .connect_kwargs attributewise, but otherwise it feels better to do it
        # early instead of late.
        constructor_kwargs = connect_kwargs or {}
        config_kwargs = self.config.connect_kwargs
        constructor_keys = constructor_kwargs.get("key_filename", [])
        config_keys = config_kwargs.get("key_filename", [])
        ssh_config_keys = self.ssh_config.get("identityfile", [])

        # Default data: constructor if given, config otherwise
        final_kwargs = constructor_kwargs or config_kwargs

        # Key filename: merge, in order, config (which includes CLI flags),
        # then constructor kwargs, and finally SSH config file data.
        # Make sure all are normalized to list as well!
        final_keys = []
        for value in (config_keys, constructor_keys, ssh_config_keys):
            if isinstance(value, string_types):
                value = [value]
            final_keys.extend(value)
        # Only populate if non-empty.
        if final_keys:
            final_kwargs["key_filename"] = final_keys

        return final_kwargs

    def get_gateway(self):
        # SSH config wins over Invoke-style config
        if "proxyjump" in self.ssh_config:
            # Reverse hop1,hop2,hop3 style ProxyJump directive so we start
            # with the final (itself non-gatewayed) hop and work up to
            # the front (actual, supplied as our own gateway) hop
            hops = reversed(self.ssh_config["proxyjump"].split(","))
            prev_gw = None
            for hop in hops:
                # Short-circuit if we appear to be our own proxy, which would
                # be a RecursionError. Implies SSH config wildcards.
                # TODO: in an ideal world we'd check user/port too in case they
                # differ, but...seriously? They can file a PR with those extra
                # half dozen test cases in play, E_NOTIME
                if self.derive_shorthand(hop)["host"] == self.host:
                    return None
                # Happily, ProxyJump uses identical format to our host
                # shorthand...
                kwargs = dict(config=self.config.clone())
                if prev_gw is not None:
                    kwargs["gateway"] = prev_gw
                cxn = Connection(hop, **kwargs)
                prev_gw = cxn
            return prev_gw
        elif "proxycommand" in self.ssh_config:
            # Just a string, which we interpret as a proxy command..
            return self.ssh_config["proxycommand"]
        # Fallback: config value (may be None).
        return self.config.gateway

    def __repr__(self):
        # Host comes first as it's the most common differentiator by far
        bits = [("host", self.host)]
        # TODO: maybe always show user regardless? Explicit is good...
        if self.user != self.config.user:
            bits.append(("user", self.user))
        # TODO: harder to make case for 'always show port'; maybe if it's
        # non-22 (even if config has overridden the local default)?
        if self.port != self.config.port:
            bits.append(("port", self.port))
        # NOTE: sometimes self.gateway may be eg False if someone wants to
        # explicitly override a configured non-None value (as otherwise it's
        # impossible for __init__ to tell if a None means "nothing given" or
        # "seriously please no gatewaying". So, this must always be a vanilla
        # truth test and not eg "is not None".
        if self.gateway:
            # Displaying type because gw params would probs be too verbose
            val = "proxyjump"
            if isinstance(self.gateway, string_types):
                val = "proxycommand"
            bits.append(("gw", val))
        return "<Connection {}>".format(
            " ".join("{}={}".format(*x) for x in bits)
        )

    def _identity(self):
        # TODO: consider including gateway and maybe even other init kwargs?
        # Whether two cxns w/ same user/host/port but different
        # gateway/keys/etc, should be considered "the same", is unclear.
        return (self.host, self.user, self.port)

    def __eq__(self, other):
        if not isinstance(other, Connection):
            return False
        return self._identity() == other._identity()

    def __lt__(self, other):
        return self._identity() < other._identity()

    def __hash__(self):
        # NOTE: this departs from Context/DataProxy, which is not usefully
        # hashable.
        return hash(self._identity())

    def derive_shorthand(self, host_string):
        # NOTE: used to be defined inline; preserving API call for both
        # backwards compatibility and because it seems plausible we may want to
        # modify behavior later, using eg config or other attributes.
        return derive_shorthand(host_string)

    @property
    def is_connected(self):
        """
        Whether or not this connection is actually open.

        .. versionadded:: 2.0
        """
        return self.transport.active if self.transport else False

    def open(self):
        """
        Initiate an SSH connection to the host/port this object is bound to.

        This may include activating the configured gateway connection, if one
        is set.

        Also saves a handle to the now-set Transport object for easier access.

        Various connect-time settings (and/or their corresponding :ref:`SSH
        config options <ssh-config>`) are utilized here in the call to
        `SSHClient.connect <paramiko.client.SSHClient.connect>`. (For details,
        see :doc:`the configuration docs </concepts/configuration>`.)

        .. versionadded:: 2.0
        """
        # Short-circuit
        if self.is_connected:
            return
        err = "Refusing to be ambiguous: connect() kwarg '{}' was given both via regular arg and via connect_kwargs!"  # noqa
        # These may not be given, period
        for key in """
            hostname
            port
            username
        """.split():
            if key in self.connect_kwargs:
                raise ValueError(err.format(key))
        # These may be given one way or the other, but not both
        if (
            "timeout" in self.connect_kwargs
            and self.connect_timeout is not None
        ):
            raise ValueError(err.format("timeout"))
        # No conflicts -> merge 'em together
        kwargs = dict(
            self.connect_kwargs,
            username=self.user,
            hostname=self.host,
            port=self.port,
        )
        if self.gateway:
            kwargs["sock"] = self.open_gateway()
        if self.connect_timeout:
            kwargs["timeout"] = self.connect_timeout
        # Strip out empty defaults for less noisy debugging
        if "key_filename" in kwargs and not kwargs["key_filename"]:
            del kwargs["key_filename"]
        # Actually connect!
        self.client.connect(**kwargs)
        self.transport = self.client.get_transport()

    def open_gateway(self):
        """
        Obtain a socket-like object from `gateway`.

        :returns:
            A ``direct-tcpip`` `paramiko.channel.Channel`, if `gateway` was a
            `.Connection`; or a `~paramiko.proxy.ProxyCommand`, if `gateway`
            was a string.

        .. versionadded:: 2.0
        """
        # ProxyCommand is faster to set up, so do it first.
        if isinstance(self.gateway, string_types):
            # Leverage a dummy SSHConfig to ensure %h/%p/etc are parsed.
            # TODO: use real SSH config once loading one properly is
            # implemented.
            ssh_conf = SSHConfig()
            dummy = "Host {}\n    ProxyCommand {}"
            ssh_conf.parse(StringIO(dummy.format(self.host, self.gateway)))
            return ProxyCommand(ssh_conf.lookup(self.host)["proxycommand"])
        # Handle inner-Connection gateway type here.
        # TODO: logging
        self.gateway.open()
        # TODO: expose the opened channel itself as an attribute? (another
        # possible argument for separating the two gateway types...) e.g. if
        # someone wanted to piggyback on it for other same-interpreter socket
        # needs...
        # TODO: and the inverse? allow users to supply their own socket/like
        # object they got via $WHEREEVER?
        # TODO: how best to expose timeout param? reuse general connection
        # timeout from config?
        return self.gateway.transport.open_channel(
            kind="direct-tcpip",
            dest_addr=(self.host, int(self.port)),
            # NOTE: src_addr needs to be 'empty but not None' values to
            # correctly encode into a network message. Theoretically Paramiko
            # could auto-interpret None sometime & save us the trouble.
            src_addr=("", 0),
        )

    def close(self):
        """
        Terminate the network connection to the remote end, if open.

        If no connection is open, this method does nothing.

        .. versionadded:: 2.0
        """
        if self.is_connected:
            self.client.close()
            if self.forward_agent and self._agent_handler is not None:
                self._agent_handler.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    @opens
    def create_session(self):
        channel = self.transport.open_session()
        if self.forward_agent:
            self._agent_handler = AgentRequestHandler(channel)
        return channel

    def _remote_runner(self):
        return self.config.runners.remote(
            context=self, inline_env=self.inline_ssh_env
        )

    @opens
    def run(self, command, **kwargs):
        """
        Execute a shell command on the remote end of this connection.

        This method wraps an SSH-capable implementation of
        `invoke.runners.Runner.run`; see its documentation for details.

        .. warning::
            There are a few spots where Fabric departs from Invoke's default
            settings/behaviors; they are documented under
            `.Config.global_defaults`.

        .. versionadded:: 2.0
        """
        return self._run(self._remote_runner(), command, **kwargs)

    @opens
    def sudo(self, command, **kwargs):
        """
        Execute a shell command, via ``sudo``, on the remote end.

        This method is identical to `invoke.context.Context.sudo` in every way,
        except in that -- like `run` -- it honors per-host/per-connection
        configuration overrides in addition to the generic/global ones. Thus,
        for example, per-host sudo passwords may be configured.

        .. versionadded:: 2.0
        """
        return self._sudo(self._remote_runner(), command, **kwargs)

    @opens
    def shell(self, **kwargs):
        """
        Run an interactive login shell on the remote end, as with ``ssh``.

        This method is intended strictly for use cases where you can't know
        what remote shell to invoke, or are connecting to a non-POSIX-server
        environment such as a network appliance or other custom SSH server.
        Nearly every other use case, including interactively-focused ones, will
        be better served by using `run` plus an explicit remote shell command
        (eg ``bash``).

        `shell` has the following differences in behavior from `run`:

        - It still returns a `~invoke.runners.Result` instance, but the object
          will have a less useful set of attributes than with `run` or `local`:

            - ``command`` will be ``None``, as there is no such input argument.
            - ``stdout`` will contain a full record of the session, including
              all interactive input, as that is echoed back to the user. This
              can be useful for logging but is much less so for doing
              programmatic things after the method returns.
            - ``stderr`` will always be empty (same as `run` when
              ``pty==True``).
            - ``pty`` will always be True (because one was automatically used).
            - ``exited`` and similar attributes will only reflect the overall
              session, which may vary by shell or appliance but often has no
              useful relationship with the internally executed commands' exit
              codes.

        - This method behaves as if ``warn`` is set to ``True``: even if the
          remote shell exits uncleanly, no exception will be raised.
        - A pty is always allocated remotely, as with ``pty=True`` under `run`.
        - The ``inline_env`` setting is ignored, as there is no default shell
          command to add the parameters to (and no guarantee the remote end
          even is a shell!)

        It supports **only** the following kwargs, which behave identically to
        their counterparts in `run` unless otherwise stated:

        - ``encoding``
        - ``env``
        - ``in_stream`` (useful in niche cases, but make sure regular `run`
          with this argument isn't more suitable!)
        - ``replace_env``
        - ``watchers`` (note that due to pty echoing your stdin back to stdout,
          a watcher will see your input as well as program stdout!)

        Those keyword arguments also honor the ``run.*`` configuration tree, as
        in `run`/`sudo`.

        :returns: `~invoke.runners.Result`

        :raises:
            `~invoke.exceptions.ThreadException` (if the background I/O threads
            encountered exceptions other than
            `~invoke.exceptions.WatcherError`).

        .. versionadded:: 2.7
        """
        runner = self.config.runners.remote_shell(context=self)
        # Reinstate most defaults as explicit kwargs to ensure user's config
        # doesn't make this mode break horribly. Then override a few that need
        # to change, like pty.
        allowed = ("encoding", "env", "in_stream", "replace_env", "watchers")
        new_kwargs = {}
        for key, value in self.config.global_defaults()["run"].items():
            if key in allowed:
                # Use allowed kwargs if given, otherwise also fill them from
                # defaults
                new_kwargs[key] = kwargs.pop(key, self.config.run[key])
            else:
                new_kwargs[key] = value
        new_kwargs.update(pty=True)
        # At this point, any leftover kwargs would be ignored, so yell instead
        if kwargs:
            err = "shell() got unexpected keyword arguments: {!r}"
            raise TypeError(err.format(list(kwargs.keys())))
        return runner.run(command=None, **new_kwargs)

    def local(self, *args, **kwargs):
        """
        Execute a shell command on the local system.

        This method is effectively a wrapper of `invoke.run`; see its docs for
        details and call signature.

        .. versionadded:: 2.0
        """
        # Superclass run() uses runners.local, so we can literally just call it
        # straight.
        return super(Connection, self).run(*args, **kwargs)

    @opens
    def sftp(self):
        """
        Return a `~paramiko.sftp_client.SFTPClient` object.

        If called more than one time, memoizes the first result; thus, any
        given `.Connection` instance will only ever have a single SFTP client,
        and state (such as that managed by
        `~paramiko.sftp_client.SFTPClient.chdir`) will be preserved.

        .. versionadded:: 2.0
        """
        if self._sftp is None:
            self._sftp = self.client.open_sftp()
        return self._sftp

    def get(self, *args, **kwargs):
        """
        Get a remote file to the local filesystem or file-like object.

        Simply a wrapper for `.Transfer.get`. Please see its documentation for
        all details.

        .. versionadded:: 2.0
        """
        return Transfer(self).get(*args, **kwargs)

    def put(self, *args, **kwargs):
        """
        Put a local file (or file-like object) to the remote filesystem.

        Simply a wrapper for `.Transfer.put`. Please see its documentation for
        all details.

        .. versionadded:: 2.0
        """
        return Transfer(self).put(*args, **kwargs)

    # TODO: yield the socket for advanced users? Other advanced use cases
    # (perhaps factor out socket creation itself)?
    # TODO: probably push some of this down into Paramiko
    @contextmanager
    @opens
    def forward_local(
        self,
        local_port,
        remote_port=None,
        remote_host="localhost",
        local_host="localhost",
    ):
        """
        Open a tunnel connecting ``local_port`` to the server's environment.

        For example, say you want to connect to a remote PostgreSQL database
        which is locked down and only accessible via the system it's running
        on. You have SSH access to this server, so you can temporarily make
        port 5432 on your local system act like port 5432 on the server::

            import psycopg2
            from fabric import Connection

            with Connection('my-db-server').forward_local(5432):
                db = psycopg2.connect(
                    host='localhost', port=5432, database='mydb'
                )
                # Do things with 'db' here

        This method is analogous to using the ``-L`` option of OpenSSH's
        ``ssh`` program.

        :param int local_port: The local port number on which to listen.

        :param int remote_port:
            The remote port number. Defaults to the same value as
            ``local_port``.

        :param str local_host:
            The local hostname/interface on which to listen. Default:
            ``localhost``.

        :param str remote_host:
            The remote hostname serving the forwarded remote port. Default:
            ``localhost`` (i.e., the host this `.Connection` is connected to.)

        :returns:
            Nothing; this method is only useful as a context manager affecting
            local operating system state.

        .. versionadded:: 2.0
        """
        if not remote_port:
            remote_port = local_port

        # TunnelManager does all of the work, sitting in the background (so we
        # can yield) and spawning threads every time somebody connects to our
        # local port.
        finished = Event()
        manager = TunnelManager(
            local_port=local_port,
            local_host=local_host,
            remote_port=remote_port,
            remote_host=remote_host,
            # TODO: not a huge fan of handing in our transport, but...?
            transport=self.transport,
            finished=finished,
        )
        manager.start()

        # Return control to caller now that things ought to be operational
        try:
            yield
        # Teardown once user exits block
        finally:
            # Signal to manager that it should close all open tunnels
            finished.set()
            # Then wait for it to do so
            manager.join()
            # Raise threading errors from within the manager, which would be
            # one of:
            # - an inner ThreadException, which was created by the manager on
            # behalf of its Tunnels; this gets directly raised.
            # - some other exception, which would thus have occurred in the
            # manager itself; we wrap this in a new ThreadException.
            # NOTE: in these cases, some of the metadata tracking in
            # ExceptionHandlingThread/ExceptionWrapper/ThreadException (which
            # is useful when dealing with multiple nearly-identical sibling IO
            # threads) is superfluous, but it doesn't feel worth breaking
            # things up further; we just ignore it for now.
            wrapper = manager.exception()
            if wrapper is not None:
                if wrapper.type is ThreadException:
                    raise wrapper.value
                else:
                    raise ThreadException([wrapper])

            # TODO: cancel port forward on transport? Does that even make sense
            # here (where we used direct-tcpip) vs the opposite method (which
            # is what uses forward-tcpip)?

    # TODO: probably push some of this down into Paramiko
    @contextmanager
    @opens
    def forward_remote(
        self,
        remote_port,
        local_port=None,
        remote_host="127.0.0.1",
        local_host="localhost",
    ):
        """
        Open a tunnel connecting ``remote_port`` to the local environment.

        For example, say you're running a daemon in development mode on your
        workstation at port 8080, and want to funnel traffic to it from a
        production or staging environment.

        In most situations this isn't possible as your office/home network
        probably blocks inbound traffic. But you have SSH access to this
        server, so you can temporarily make port 8080 on that server act like
        port 8080 on your workstation::

            from fabric import Connection

            c = Connection('my-remote-server')
            with c.forward_remote(8080):
                c.run("remote-data-writer --port 8080")
                # Assuming remote-data-writer runs until interrupted, this will
                # stay open until you Ctrl-C...

        This method is analogous to using the ``-R`` option of OpenSSH's
        ``ssh`` program.

        :param int remote_port: The remote port number on which to listen.

        :param int local_port:
            The local port number. Defaults to the same value as
            ``remote_port``.

        :param str local_host:
            The local hostname/interface the forwarded connection talks to.
            Default: ``localhost``.

        :param str remote_host:
            The remote interface address to listen on when forwarding
            connections. Default: ``127.0.0.1`` (i.e. only listen on the remote
            localhost).

        :returns:
            Nothing; this method is only useful as a context manager affecting
            local operating system state.

        .. versionadded:: 2.0
        """
        if not local_port:
            local_port = remote_port
        # Callback executes on each connection to the remote port and is given
        # a Channel hooked up to said port. (We don't actually care about the
        # source/dest host/port pairs at all; only whether the channel has data
        # to read and suchlike.)
        # We then pair that channel with a new 'outbound' socket connection to
        # the local host/port being forwarded, in a new Tunnel.
        # That Tunnel is then added to a shared data structure so we can track
        # & close them during shutdown.
        #
        # TODO: this approach is less than ideal because we have to share state
        # between ourselves & the callback handed into the transport's own
        # thread handling (which is roughly analogous to our self-controlled
        # TunnelManager for local forwarding). See if we can use more of
        # Paramiko's API (or improve it and then do so) so that isn't
        # necessary.
        tunnels = []

        def callback(channel, src_addr_tup, dst_addr_tup):
            sock = socket.socket()
            # TODO: handle connection failure such that channel, etc get closed
            sock.connect((local_host, local_port))
            # TODO: we don't actually need to generate the Events at our level,
            # do we? Just let Tunnel.__init__ do it; all we do is "press its
            # button" on shutdown...
            tunnel = Tunnel(channel=channel, sock=sock, finished=Event())
            tunnel.start()
            # Communication between ourselves & the Paramiko handling subthread
            tunnels.append(tunnel)

        # Ask Paramiko (really, the remote sshd) to call our callback whenever
        # connections are established on the remote iface/port.
        # transport.request_port_forward(remote_host, remote_port, callback)
        try:
            self.transport.request_port_forward(
                address=remote_host, port=remote_port, handler=callback
            )
            yield
        finally:
            # TODO: see above re: lack of a TunnelManager
            # TODO: and/or also refactor with TunnelManager re: shutdown logic.
            # E.g. maybe have a non-thread TunnelManager-alike with a method
            # that acts as the callback? At least then there's a tiny bit more
            # encapsulation...meh.
            for tunnel in tunnels:
                tunnel.finished.set()
                tunnel.join()
            self.transport.cancel_port_forward(
                address=remote_host, port=remote_port
            )
