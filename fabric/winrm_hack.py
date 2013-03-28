import collections
import sys
import threading
import time
import Queue

from fabric.io import output_loop
from fabric.state import env
from fabric.thread_handling import ThreadHandler

import winrm.winrm_service

class WinRMWebServiceWrapper(object):
    def __init__(self, host, username, password, timeout=None):
        self.client = winrm.winrm_service.WinRMWebService(
                endpoint="http://{0}:5985/wsman".format(host),
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

class _StreamData(object):
    def __init__(self, queue, buffer_size):
        self.queue = queue
        self.fifo = collections.deque(maxlen=buffer_size)
        self.is_done = False

class WinRMChannel(object):
    """Dummy winrm 'channel' that mimics an ssh channel API.
    
    Note
    ----
    because of limitations in winrm API, streams cannot be handled in different
    threads: both stdout and stderr are updated in a single call
    """
    def __init__(self, stdout_queue, stderr_queue):
        self.buffer_size = 4096

        self._stdout = _StreamData(stdout_queue, self.buffer_size)
        self._stderr = _StreamData(stderr_queue, self.buffer_size)

        self._recv_lock = threading.Lock()

    def _recv(self, nbytes, stream_data):
        with self._recv_lock:
            if nbytes > self.buffer_size:
                raise ValueError("Too many bytes requested !")
            if stream_data.is_done:
                return ""
            ret = []
            for i in range(min(len(stream_data.fifo), nbytes)):
                ret.append(stream_data.fifo.popleft())

            while len(ret) < nbytes:
                new_data, is_done = stream_data.queue.get()
                needs_to_buffer = len(new_data) + len(ret) > nbytes
                if needs_to_buffer:
                    to_buffer = new_data[nbytes - len(ret):]
                    ret.extend(new_data[:nbytes - len(ret)])
                    stream_data.fifo.extend(to_buffer)
                else:
                    ret.extend(new_data)
                stream_data.queue.task_done()
                if is_done:
                    stream_data.is_done = True
                    break
            return "".join(ret)

    def recv(self, nbytes):
        return self._recv(nbytes, self._stdout)

    def recv_stderr(self, nbytes):
        return self._recv(nbytes, self._stderr)

def execute_winrm_command(host, command, combine_stderr=None, stdout=None,
        stderr=None, timeout=None):
    # stdout/stderr redirection
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    invoke_shell = False
    remote_interrupt = False

    stdout_queue = Queue.Queue()
    stderr_queue = Queue.Queue()

    winrm_service = WinRMWebServiceWrapper(host, env.user, env.password, timeout=timeout)

    with winrm_service.exec_command(command=command) as winrm_command:
        stdout_buffer, stderr_buffer = [], []

        streams_channel = WinRMChannel(stdout_queue, stderr_queue)

        workers = (
            ThreadHandler('out', output_loop, streams_channel, "recv",
                capture=stdout_buffer, stream=stdout, timeout=timeout),
            ThreadHandler('err', output_loop, streams_channel, "recv_stderr",
                capture=stderr_buffer, stream=stderr, timeout=timeout),
        )

        is_done = False
        while not is_done:
            _stdout, _stderr, status, is_done = winrm_command._raw_get_command_output()
            stdout_queue.put((_stdout, is_done))
            stderr_queue.put((_stderr, is_done))

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
