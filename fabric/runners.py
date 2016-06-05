import time

from invoke import Runner, pty_size, Result as InvokeResult
from paramiko import io_sleep


class Remote(Runner):
    """
    Run a shell command over an SSH connection.

    This class subclasses `invoke.runners.Runner`; please see its documentation
    for most public API details.

    .. note::
        `.Remote`'s ``__init__`` method expects a `.Connection` (or subclass)
        instance for its ``context`` argument.
    """
    def start(self, command, shell, env):
        self.channel = self.context._create_session()
        if self.using_pty:
            rows, cols = pty_size()
            self.channel.get_pty(width=rows, height=cols)
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
            self.channel.send(u'\x03')
        else:
            raise interrupt

    def returncode(self):
        return self.channel.recv_exit_status()

    def generate_result(self, **kwargs):
        kwargs['connection'] = self.context
        return Result(**kwargs)


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


class RemoteSudo(Remote):
    """
    Run a command over SSH, wrapped in ``sudo``.
    """
    # Needs to do what Remote does, except:
    # * modify the command string (implies that's a subroutine or hooks based
    # thing)
    # * handle password prompting and playback (prob also a subroutine?)
    # TODO: this may want to just become generic except-like handling (like fab
    # 1 'prompts' stuff) in Remote, then this simply automates wrapping w/ sudo
    # -c (i.e. one could get 100% same effect by manually doing run("sudo -c
    # 'my command'")).
    # TODO: that probably just means a method on Connection and no new class
    # here.
    pass


class Result(InvokeResult):
    """
    A `.Result` which knows about host connections and similar metadata.
    """
    def __init__(self, **kwargs):
        connection = kwargs.pop('connection')
        super(Result, self).__init__(**kwargs)
        self.connection = connection

    @property
    def host(self):
        """
        The host upon which the command was executed.
        """
        # TODO: change away from host string
        return self.connection.host_string

    # TODO: have useful str/repr differentiation from invoke.Result,
    # transfer.Result etc.
