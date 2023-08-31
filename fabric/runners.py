import signal
import threading

from invoke import Runner, pty_size, Result as InvokeResult


def cares_about_SIGWINCH():
    return (
        hasattr(signal, "SIGWINCH")
        and threading.current_thread() is threading.main_thread()
    )


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

    def __init__(self, *args, **kwargs):
        """
        Thin wrapper for superclass' ``__init__``; please see it for details.

        Additional keyword arguments defined here are listed below.

        :param bool inline_env:
            Whether to 'inline' shell env vars as prefixed parameters, instead
            of trying to submit them via `.Channel.update_environment`.
            Default: ``True``.

        .. versionchanged:: 2.3
            Added the ``inline_env`` parameter.
        .. versionchanged:: 3.0
            Changed the default value of ``inline_env`` from ``False`` to
            ``True``.
        """
        self.inline_env = kwargs.pop("inline_env", None)
        super().__init__(*args, **kwargs)

    def start(self, command, shell, env, timeout=None):
        self.channel = self.context.create_session()
        if self.using_pty:
            # Set initial size to match local size
            cols, rows = pty_size()
            self.channel.get_pty(width=cols, height=rows)
            # If platform supports, also respond to SIGWINCH (window change) by
            # sending the sshd a window-change message to update
            if cares_about_SIGWINCH():
                signal.signal(signal.SIGWINCH, self.handle_window_change)
        if env:
            # TODO: honor SendEnv from ssh_config (but if we do, _should_ we
            # honor it even when prefixing? That would depart from OpenSSH
            # somewhat (albeit as a "what we can do that it cannot" feature...)
            if self.inline_env:
                # TODO: escaping, if we can find a FOOLPROOF THIRD PARTY METHOD
                # for doing so!
                # TODO: switch to using a higher-level generic command
                # prefixing functionality, when implemented.
                parameters = " ".join(
                    ["{}={}".format(k, v) for k, v in sorted(env.items())]
                )
                # NOTE: we can assume 'export' and '&&' relatively safely, as
                # sshd always brings some shell into play, even if it's just
                # /bin/sh.
                command = "export {} && {}".format(parameters, command)
            else:
                self.channel.update_environment(env)
        self.send_start_message(command)

    def send_start_message(self, command):
        self.channel.exec_command(command)

    def run(self, command, **kwargs):
        kwargs.setdefault("replace_env", True)
        return super().run(command, **kwargs)

    def read_proc_stdout(self, num_bytes):
        return self.channel.recv(num_bytes)

    def read_proc_stderr(self, num_bytes):
        return self.channel.recv_stderr(num_bytes)

    def _write_proc_stdin(self, data):
        return self.channel.sendall(data)

    def close_proc_stdin(self):
        return self.channel.shutdown_write()

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
            self.channel.send("\x03")
        else:
            raise interrupt

    def returncode(self):
        return self.channel.recv_exit_status()

    def generate_result(self, **kwargs):
        kwargs["connection"] = self.context
        return Result(**kwargs)

    def stop(self):
        super().stop()
        if hasattr(self, "channel"):
            self.channel.close()
        if cares_about_SIGWINCH():
            signal.signal(signal.SIGWINCH, signal.SIG_DFL)

    def kill(self):
        # Just close the channel immediately, which is about as close as we can
        # get to a local SIGKILL unfortunately.
        # TODO: consider _also_ calling .send_interrupt() and only doing this
        # after another few seconds; but A) kinda fragile/complex and B) would
        # belong in invoke.Runner anyways?
        self.channel.close()

    def handle_window_change(self, signum, frame):
        """
        Respond to a `signal.SIGWINCH` (as a standard signal handler).

        Sends a window resize command via Paramiko channel method.
        """
        self.channel.resize_pty(*pty_size())

    # TODO: shit that is in fab 1 run() but could apply to invoke.Local too:
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


class RemoteShell(Remote):
    def send_start_message(self, command):
        self.channel.invoke_shell()


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
        super().__init__(**kwargs)
        self.connection = connection

    # TODO: have useful str/repr differentiation from invoke.Result,
    # transfer.Result etc.
