from invoke import Runner, pty_size, Result as InvokeResult


class Remote(Runner):
    """
    Run a shell command over an SSH connection.

    This class subclasses `invoke.runners.Runner`; please see its documentation
    for most public API details.

    .. note::
        `.Remote`'s ``__init__`` method expects a `.Connection` (or subclass)
        instance for its ``context`` argument.

    .. versionadded:: 2.0
    """

    def start(self, command, shell, env):
        self.channel = self.context.create_session()
        if self.using_pty:
            rows, cols = pty_size()
            self.channel.get_pty(width=rows, height=cols)
        # TODO: consider adding an option to conditionally turn this
        # update_environment call into a command-string prefixing behavior
        # instead (e.g. when one isn't able/willing to update remote server's
        # AcceptEnv setting). OR: rely on higher-level generic command
        # prefixing functionality, when implemented.
        # TODO: honor SendEnv from ssh_config
        self.channel.update_environment(env)
        # TODO: pass in timeout= here when invoke grows timeout functionality
        # in Runner/Local.
        self.channel.exec_command(command)

    def read_proc_stdout(self, num_bytes):
        return self.channel.recv(num_bytes)

    def read_proc_stderr(self, num_bytes):
        return self.channel.recv_stderr(num_bytes)

    def _write_proc_stdin(self, data):
        return self.channel.sendall(data)

    @property
    def process_is_finished(self):
        return self.channel.exit_status_ready()

    def send_interrupt(self, interrupt):
        # NOTE: in v1, we just reraised the KeyboardInterrupt unless a PTY was
        # present; this seems to have been because without a PTY, the
        # below escape sequence is ignored, so all we can do is immediately
        # terminate on our end.
        # NOTE: also in v1, the raising of the KeyboardInterrupt completely
        # skipped all thread joining & cleanup; presumably regular interpreter
        # shutdown suffices to tie everything off well enough.
        if self.using_pty:
            # Submit hex ASCII character 3, aka ETX, which most Unix PTYs
            # interpret as a foreground SIGINT.
            # TODO: is there anything else we can do here to be more portable?
            self.channel.send(u"\x03")
        else:
            raise interrupt

    def returncode(self):
        return self.channel.recv_exit_status()

    def generate_result(self, **kwargs):
        kwargs["connection"] = self.context
        return Result(**kwargs)

    def stop(self):
        if hasattr(self, "channel"):
            self.channel.close()

    # TODO: shit that is in fab 1 run() but could apply to invoke.Local too:
    # * command timeout control
    # * see rest of stuff in _run_command/_execute in operations.py...there is
    # a bunch that applies generally like optional exit codes, etc

    # TODO: general shit not done yet
    # * stdin; Local relies on local process management to ensure stdin is
    # hooked up; we cannot do that.
    # * output prefixing
    # * agent forwarding
    # * reading at 4096 bytes/time instead of whatever inv defaults to (also,
    # document why we are doing that, iirc it changed recentlyish via ticket)
    # * TODO: oh god so much more, go look it up

    # TODO: shit that has no Local equivalent that we probs need to backfill
    # into Runner, probably just as a "finish()" or "stop()" (to mirror
    # start()):
    # * channel close()
    # * agent-forward close()


class Result(InvokeResult):
    """
    An `invoke.runners.Result` exposing which `.Connection` was run against.

    Exposes all attributes from its superclass, then adds a ``.connection``,
    which is simply a reference to the `.Connection` whose method yielded this
    result.

    .. versionadded:: 2.0
    """

    def __init__(self, **kwargs):
        connection = kwargs.pop("connection")
        super(Result, self).__init__(**kwargs)
        self.connection = connection

    # TODO: have useful str/repr differentiation from invoke.Result,
    # transfer.Result etc.
