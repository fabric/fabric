from functools import partial
import time

from invoke.runners import Runner
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
    def run_direct(self, command, warn, hide, encoding):
        channel = self.context._create_session()
        channel.exec_command(command)

        #   (TODO: host prefixes depending on configuration)
        # create thread objects, add to list, start them
        # wait on remote proc (may require loop+sleep)
        # join threads
        # tie up captured stderr/out into single string objs
        # return those + exit code (+ exception? does that make sense here as
        #    well as wherever it was originally intended in Local?)

        return ("", "", 0, None)

    def start(self, command):
        # TODO: pty setup
        self.channel = self.context._create_session()
        self.channel.exec_command(command)

    def stdout_reader(self):
        return self.channel.recv

    def stderr_reader(self):
        return self.channel.recv_stderr

    def default_encoding(self):
        # TODO: this could be hairy or impossible!
        return "utf-8"

    def wait(self):
        while True:
            # TODO: fab1 workers raise_if_needed == ???
            if self.channel.exit_status_ready():
                return
            # TODO: try/except KeyboardInterrupt around the sleep - necessary,
            # but also make sure there's no open tickets about doing this
            # better/different. (Also, see remote_interrupt)
            # TODO: where to access paramiko (for io_sleep)? here or via
            # something in Connection? (basically, how hard should Connection
            # encapsulate paramiko things?)
            time.sleep(io_sleep)

    def returncode(self):
        return self.channel.recv_exit_status()

    # TODO: shit that is in fab 1 run() but could apply to invoke.Local too:
    # * command timeout control
    # * see rest of stuff in _run_command/_execute in operations.py...there is
    # a bunch that applies generally like optional exit codes, etc

    # TODO: general shit not done yet
    # * stdin; Local relies on local process management to ensure stdin is
    # hooked up; we cannot do that.
    # * output prefixing
    # * agent forwarding

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
