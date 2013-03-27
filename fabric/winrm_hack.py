import sys
import threading
import time

from fabric.io import output_loop
from fabric.state import env
from fabric.thread_handling import ThreadHandler

from winrm.winrm_service import WinRMWebService

_WINRM_IO_SLEEP = 0.2

class WinRMCommand(object):
    def __init__(self, client, shell_id, command_id):
        self.client = client
        self.shell_id = shell_id
        self.command_id = command_id

        self._stdout_buffer = []
        self._stderr_buffer = []
        self._is_done = False
        self._status_code = None

        self._recv_lock = threading.Lock()

    def cleanup(self):
        self.client.cleanup_command(self.shell_id, self.command_id)
        self.client.close_shell(self.shell_id)

    def get_command_output(self):
        self._is_done = True
        return self.client.get_command_output(self.shell_id, self.command_id)

    def exit_status_ready(self):
        return self._is_done

    def recv_exit_status(self):
        while not self._is_done:
            time.sleep(0.1)
            self.poll()
            #raise ValueError("Trying to access exit status without status being ready !")
        return self._status_code

    def poll(self):
        if self._is_done:
            return
        else:
            stdout, stderr, status_code, is_done = \
                self.client._raw_get_command_output(self.shell_id, self.command_id)
            self._stdout_buffer.append(stdout)
            self._stderr_buffer.append(stderr)
            self._is_done = is_done
            if is_done:
                self._status_code = status_code

    def recv(self, nbytes=None):
        with self._recv_lock:
            # FIXME: nbytes is ignored
            self.poll()
            out = "".join(self._stdout_buffer)
            self._stdout_buffer = []
            return out

    def recv_stderr(self, nbytes=None):
        with self._recv_lock:
            # FIXME: nbytes is ignored
            self.poll()
            err = "".join(self._stderr_buffer)
            self._stderr_buffer = []
            return err

    def __enter__(self):
        return self

    def __exit__(self, *a, **kw):
        self.cleanup()

class DummyChannel(object):
    def __init__(self, host, username, password, timeout=None):
        self.client = WinRMWebService(endpoint="http://{0}:5985/wsman".format(host),
                transport="plaintext",
                username=username,
                password=password)
        if timeout is not None:
            self.client.set_timeout(timeout)
        else:
            self.client.set_timeout(3600)

    def exec_command(self, command):
        shell_id = self.client.open_shell()
        command_id = self.client.run_command(shell_id, command, [])
        return WinRMCommand(self.client, shell_id, command_id)

def execute_winrm_command(host, command, combine_stderr=None, stdout=None,
        stderr=None, timeout=None):
    # stdout/stderr redirection
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    invoke_shell = False
    remote_interrupt = False

    channel = DummyChannel(host, env.user, env.password, timeout=timeout)

    with channel.exec_command(command=command) as winrm_command:
        stdout_buffer, stderr_buffer = [], []

        workers = (
            ThreadHandler('out', output_loop, winrm_command, "recv",
                capture=stdout_buffer, stream=stdout, timeout=timeout),
            ThreadHandler('err', output_loop, winrm_command, "recv_stderr",
                capture=stderr_buffer, stream=stderr, timeout=timeout),
        )

        while True:
            if winrm_command.exit_status_ready():
                break
            else:
                # Check for thread exceptions here so we can raise ASAP
                # (without chance of getting blocked by, or hidden by an
                # exception within, recv_exit_status())
                for worker in workers:
                    worker.raise_if_needed()
            try:
                time.sleep(_WINRM_IO_SLEEP)
            except KeyboardInterrupt:
                if not remote_interrupt:
                    raise
                raise NotImplementedError()

        status = winrm_command.recv_exit_status()

        # Wait for threads to exit so we aren't left with stale threads
        for worker in workers:
            worker.thread.join()
            worker.raise_if_needed()

        # Update stdout/stderr with captured values if applicable
        if not invoke_shell:
            stdout_buf = ''.join(stdout_buffer).strip()
            stderr_buf = ''.join(stderr_buffer).strip()
        else:
            raise NotImplementedError()

        return stdout_buf, stderr_buf, status
