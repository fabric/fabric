from invoke.vendor.six import StringIO

from spec import Spec, ok_, eq_
from invoke import pty_size, Result

from fabric.connection import Connection
from fabric.runners import Remote
from fabric.utils import get_local_user

from _utils import mock_remote


# On most systems this will explode if actually executed as a shell command;
# this lets us detect holes in our network mocking.
CMD = "nope"


class Remote_(Spec):
    def needs_handle_on_a_Connection(self):
        c = Connection('host')
        ok_(Remote(context=c).context is c)

    class run:
        @mock_remote()
        def calls_expected_paramiko_bits(self, chan):
            c = Connection('host')
            r = Remote(context=c)
            r.run(CMD)
            # mock_remote() makes generic sanity checks like "were
            # get_transport and open_session called", but we also want to make
            # sure that exec_command got run with our arg to run().
            chan.exec_command.assert_called_with(CMD)

        @mock_remote(out="hello yes this is dog")
        def writes_remote_streams_to_local_streams(self, chan):
            c = Connection('host')
            r = Remote(context=c)
            fakeout = StringIO()
            r.run(CMD, out_stream=fakeout)
            eq_(fakeout.getvalue(), "hello yes this is dog")

        @mock_remote()
        def pty_True_uses_paramiko_get_pty(self, chan):
            c = Connection('host')
            r = Remote(context=c)
            r.run(CMD, pty=True)
            cols, rows = pty_size()
            chan.get_pty.assert_called_with(width=cols, height=rows)

        @mock_remote(out="some text", wait=1)
        def wait_loop_performs_io_sleep(self, chan):
            c = Connection('host')
            r = Remote(context=c)
            fakeout = StringIO()
            r.run(CMD, out_stream=fakeout)
            eq_(fakeout.getvalue(), "some text")

        @mock_remote()
        def return_value_is_Result_subclass_exposing_host_used(self, chan):
            c = Connection('host')
            r = Remote(context=c)
            result = r.run(CMD)
            ok_(isinstance(result, Result))
            # Mild sanity test for other Result superclass bits
            eq_(result.ok, True)
            eq_(result.exited, 0)
            # Test the attr our own subclass adds
            eq_(result.host, "{0}@host:22".format(get_local_user()))

        # TODO: how much of Invoke's tests re: the upper level run() (re:
        # things like returning Result, behavior of Result, etc) to
        # duplicate here? Ideally none or very few core ones.

        # TODO: only test guts of our stuff, Invoke's Runner tests should
        # handle all the normal shit like stdout/err print and capture.
        # Implies we want a way to import & run those tests ourselves, though,
        # with the Runner instead being a Remote. Or do we just replicate the
        # basics?

        # TODO: all other run() tests from fab1...


class RemoteSudo_(Spec):
    # * wrapper/preparation method now adds sudo wrapper too
    # * works well with bash/etc wrapping
    # * can auto-respond with password
    # * prompts terminal (mock?) if no stored password
    # * stored password works on per connection object basis (talks to
    #   connection/context?)
    pass
