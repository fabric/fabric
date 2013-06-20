import sys

from fabric.state import env

import winrm.winrm_service

class WinRMWebServiceWrapper(object):
    def __init__(self, host, username, password, timeout=None, port=5985):
        self.client = winrm.winrm_service.WinRMWebService(
                endpoint="http://{0}:{1}/wsman".format(host, port),
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
        return _WinRMCommandWrapper(self.client, shell_id, command_id)

class _WinRMCommandWrapper(object):
    """Wrapper around a single winrm command to ensure proper cleanup."""
    def __init__(self, client, shell_id, command_id):
        self.client = client
        self.shell_id = shell_id
        self.command_id = command_id

    def cleanup(self):
        self.client.cleanup_command(self.shell_id, self.command_id)
        self.client.close_shell(self.shell_id)

    def get_command_output(self):
        return self.client.get_command_output(self.shell_id, self.command_id)

    def _raw_get_command_output(self):
        return self.client._raw_get_command_output(self.shell_id, self.command_id)

    def __enter__(self):
        return self

    def __exit__(self, *a, **kw):
        self.cleanup()

def execute_winrm_command(host, command, combine_stderr=None, stdout=None,
        stderr=None, timeout=None, port=5985):
    # stdout/stderr redirection
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    if combine_stderr is None:
        combine_stderr = env.combine_stderr

    invoke_shell = False
    remote_interrupt = False

    winrm_service = WinRMWebServiceWrapper(host, env.user, env.password, timeout=timeout, port=port)

    with winrm_service.exec_command(command=command) as winrm_command:
        stdout_buffer, stderr_buffer = [], []

        is_done = False
        while not is_done:
            _stdout, _stderr, status, is_done = winrm_command._raw_get_command_output()
            for (buf, stream, prefix) in ((_stdout, stdout, "out"), (_stderr, stderr, "err")):
                lines = buf.splitlines()
                for line in lines[:-1]:
                    stream.write("[{}] {}: {}\n".format(env.host_string, prefix, line))
                if lines:
                    if buf.endswith("\n"):
                        suffix = "\n"
                    else:
                        suffix = ""
                    stream.write("[{}] {}: {}{}".format(env.host_string, prefix, lines[-1], suffix))

        # Update stdout/stderr with captured values if applicable
        if not invoke_shell:
            stdout_buf = ''.join(stdout_buffer).strip()
            stderr_buf = ''.join(stderr_buffer).strip()
        else:
            raise NotImplementedError()

        return stdout_buf, stderr_buf, status
