from invoke.vendor.six import StringIO

from spec import Spec, skip, ok_, eq_
from mock import Mock, patch

from fabric.connection import Connection
from fabric.runners import Remote, RemoteSudo

from _utils import mock_remote


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

        def pty_True_uses_paramiko_get_pty(self):
            skip()

        # TODO: how much of Invoke's tests re: the upper level run() (re:
        # things like returning Result, behavior of Result, etc) to
        # duplicate here? Ideally none or very few core ones.

        # TODO: do we need custom extensions to Result (which our tutorial
        # actually claims we have - check if there are actually any differences
        # from the core one at this point, because there might not be?)

        # TODO: only test guts of our stuff, Invoke's Runner tests should
        # handle all the normal shit like stdout/err print and capture.
        # Implies we want a way to import & run those tests ourselves, though,
        # with the Runner instead being a Remote. Or do we just replicate the
        # basics?
        
        def may_wrap_command_with_things_like_bash_dash_c(self):
            "may wrap command with things like bash -c"
            # TODO: how? also implies top level run() wants to pass **kwargs to
            # runner somehow, though that's dangerous; maybe allow runner to
            # expose what it expects so run() can correctly determine things.
            # TODO: oughtn't this be part of invoke proper?
            skip()

        def does_not_wrap_command_by_default(self):
            skip()

        # TODO: all other run() tests from fab1...


class RemoteSudo_(Spec):
    # * wrapper/preparation method now adds sudo wrapper too
    # * works well with bash/etc wrapping
    # * can auto-respond with password
    # * prompts terminal (mock?) if no stored password
    # * stored password works on per connection object basis (talks to
    #   connection/context?)
    pass
