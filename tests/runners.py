from io import StringIO

from unittest.mock import Mock, patch
from pytest import skip  # noqa

from invoke import pty_size, Result

from fabric import Config, Connection, Remote, RemoteShell


# On most systems this will explode if actually executed as a shell command;
# this lets us detect holes in our network mocking.
CMD = "nope"

# TODO: see TODO in tests/main.py above _run_fab(), this is the same thing.
def _Connection(*args, **kwargs):
    kwargs["config"] = Config({"run": {"in_stream": False}})
    return Connection(*args, **kwargs)


def _runner():
    return Remote(context=_Connection("host"))


class Remote_:
    def needs_handle_on_a_Connection(self):
        c = _Connection("host")
        assert Remote(context=c).context is c

    class env:
        def replaces_when_replace_env_True(self, remote):
            env = _runner().run(CMD, env={"JUST": "ME"}, replace_env=True).env
            assert env == {"JUST": "ME"}

        def augments_when_replace_env_False(self, remote):
            env = _runner().run(CMD, env={"JUST": "ME"}, replace_env=False).env
            assert (
                "PATH" in env
            )  # assuming this will be in every test environment
            assert "JUST" in env
            assert env["JUST"] == "ME"

    class run:
        def calls_expected_paramiko_bits(self, remote):
            # remote mocking makes generic sanity checks like "were
            # get_transport and open_session called", but we also want to make
            # sure that exec_command got run with our arg to run().
            remote.expect(cmd=CMD)
            _runner().run(CMD)

        def writes_remote_streams_to_local_streams(self, remote):
            remote.expect(out=b"hello yes this is dog")
            fakeout = StringIO()
            _runner().run(CMD, out_stream=fakeout)
            assert fakeout.getvalue() == "hello yes this is dog"

        def return_value_is_Result_subclass_exposing_cxn_used(self, remote):
            c = _Connection("host")
            result = Remote(context=c).run(CMD)
            assert isinstance(result, Result)
            # Mild sanity test for other Result superclass bits
            assert result.ok is True
            assert result.exited == 0
            # Test the attr our own subclass adds
            assert result.connection is c

        def channel_is_closed_normally(self, remote):
            chan = remote.expect()
            # I.e. Remote.stop() closes the channel automatically
            _runner().run(CMD)
            chan.close.assert_called_once_with()

        def channel_is_closed_on_body_exceptions(self, remote):
            chan = remote.expect()

            # I.e. Remote.stop() is called within a try/finally.
            # Technically is just testing invoke.Runner, but meh.
            class Oops(Exception):
                pass

            class _OopsRemote(Remote):
                def wait(self):
                    raise Oops()

            r = _OopsRemote(context=_Connection("host"))
            try:
                r.run(CMD)
            except Oops:
                chan.close.assert_called_once_with()
            else:
                assert False, "Runner failed to raise exception!"

        def channel_close_skipped_when_channel_not_even_made(self):
            # I.e. if obtaining self.channel doesn't even happen (i.e. if
            # Connection.create_session() dies), we need to account for that
            # case...
            class Oops(Exception):
                pass

            def oops():
                raise Oops

            cxn = _Connection("host")
            cxn.create_session = oops
            # When bug present, this will result in AttributeError because
            # Remote has no 'channel'
            try:
                Remote(context=cxn).run(CMD)
            except Oops:
                pass
            else:
                assert False, "Weird, Oops never got raised..."

        class pty_True:
            def uses_paramiko_get_pty_with_local_size(self, remote):
                chan = remote.expect()
                _runner().run(CMD, pty=True)
                cols, rows = pty_size()
                chan.get_pty.assert_called_with(width=cols, height=rows)

            @patch("fabric.runners.signal")
            def no_SIGWINCH_means_no_handler(self, signal, remote):
                delattr(signal, "SIGWINCH")
                remote.expect()
                _runner().run(CMD, pty=True)
                assert not signal.signal.called

            @patch("fabric.runners.signal")
            def SIGWINCH_handled_when_present(self, signal, remote):
                remote.expect()
                runner = _runner()
                runner.run(CMD, pty=True)
                signal.signal.assert_called_once_with(
                    signal.SIGWINCH, runner.handle_window_change
                )

            def window_change_handler_uses_resize_pty(self):
                runner = _runner()
                runner.channel = Mock()
                runner.handle_window_change(None, None)
                cols, rows = pty_size()
                runner.channel.resize_pty.assert_called_once_with(cols, rows)

        # TODO: how much of Invoke's tests re: the upper level run() (re:
        # things like returning Result, behavior of Result, etc) to
        # duplicate here? Ideally none or very few core ones.

        # TODO: only test guts of our stuff, Invoke's Runner tests should
        # handle all the normal shit like stdout/err print and capture.
        # Implies we want a way to import & run those tests ourselves, though,
        # with the Runner instead being a Remote. Or do we just replicate the
        # basics?

        # TODO: all other run() tests from fab1...

    class start:
        def sends_env_to_paramiko_update_environment_by_default(self, remote):
            chan = remote.expect()
            _runner().run(CMD, env={"FOO": "bar"})
            chan.update_environment.assert_called_once_with({"FOO": "bar"})

        def uses_export_prefixing_when_inline_env_is_True(self, remote):
            chan = remote.expect(
                cmd="export DEBUG=1 PATH=/opt/bin && {}".format(CMD)
            )
            r = Remote(context=_Connection("host"), inline_env=True)
            r.run(CMD, env={"PATH": "/opt/bin", "DEBUG": "1"})
            assert not chan.update_environment.called

    def send_start_message_sends_exec_command(self):
        runner = Remote(context=None)
        runner.channel = Mock()
        runner.send_start_message(command="whatever")
        runner.channel.exec_command.assert_called_once_with("whatever")

    def kill_closes_the_channel(self):
        runner = _runner()
        runner.channel = Mock()
        runner.kill()
        runner.channel.close.assert_called_once_with()


class RemoteShell_:
    def send_start_message_sends_invoke_shell(self):
        runner = RemoteShell(context=None)
        runner.channel = Mock()
        runner.send_start_message(command=None)
        runner.channel.invoke_shell.assert_called_once_with()
