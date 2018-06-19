try:
    from invoke.vendor.six import StringIO
except ImportError:
    from six import StringIO

from invoke import pty_size, Result

from fabric import Config, Connection, Remote


# On most systems this will explode if actually executed as a shell command;
# this lets us detect holes in our network mocking.
CMD = "nope"

# TODO: see TODO in tests/main.py above _run_fab(), this is the same thing.
def _Connection(*args, **kwargs):
    kwargs["config"] = Config({"run": {"in_stream": False}})
    return Connection(*args, **kwargs)


class Remote_:

    def needs_handle_on_a_Connection(self):
        c = _Connection("host")
        assert Remote(context=c).context is c

    class run:

        def calls_expected_paramiko_bits(self, remote):
            # remote mocking makes generic sanity checks like "were
            # get_transport and open_session called", but we also want to make
            # sure that exec_command got run with our arg to run().
            remote.expect(cmd=CMD)
            c = _Connection("host")
            r = Remote(context=c)
            r.run(CMD)

        def writes_remote_streams_to_local_streams(self, remote):
            remote.expect(out=b"hello yes this is dog")
            c = _Connection("host")
            r = Remote(context=c)
            fakeout = StringIO()
            r.run(CMD, out_stream=fakeout)
            assert fakeout.getvalue() == "hello yes this is dog"

        def pty_True_uses_paramiko_get_pty(self, remote):
            chan = remote.expect()
            c = _Connection("host")
            r = Remote(context=c)
            r.run(CMD, pty=True)
            cols, rows = pty_size()
            chan.get_pty.assert_called_with(width=cols, height=rows)

        def return_value_is_Result_subclass_exposing_cxn_used(self, remote):
            c = _Connection("host")
            r = Remote(context=c)
            result = r.run(CMD)
            assert isinstance(result, Result)
            # Mild sanity test for other Result superclass bits
            assert result.ok is True
            assert result.exited == 0
            # Test the attr our own subclass adds
            assert result.connection is c

        def channel_is_closed_normally(self, remote):
            chan = remote.expect()
            # I.e. Remote.stop() closes the channel automatically
            r = Remote(context=_Connection("host"))
            r.run(CMD)
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
            r = Remote(context=cxn)
            # When bug present, this will result in AttributeError because
            # Remote has no 'channel'
            try:
                r.run(CMD)
            except Oops:
                pass
            else:
                assert False, "Weird, Oops never got raised..."

        # TODO: how much of Invoke's tests re: the upper level run() (re:
        # things like returning Result, behavior of Result, etc) to
        # duplicate here? Ideally none or very few core ones.

        # TODO: only test guts of our stuff, Invoke's Runner tests should
        # handle all the normal shit like stdout/err print and capture.
        # Implies we want a way to import & run those tests ourselves, though,
        # with the Runner instead being a Remote. Or do we just replicate the
        # basics?

        # TODO: all other run() tests from fab1...
