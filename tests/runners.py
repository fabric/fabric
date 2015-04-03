from spec import Spec, skip

from fabric.runner import Remote, RemoteSudo


class Remote_(Spec):
    def needs_handle_on_a_Connection(self):
        c = Connection('host')
        ok_(Remote(context=c).context is c)

    def uses_paramiko_exec_command(self):
        # * Patch Client.exec_command, right?
        # * Run eg Remote(context=Connection('host')).run('command')
        # * Assert exec_command called with 'command'
        # * TODO: how does this truly tie in with run_direct/run_pty?

    def run_pty_uses_paramiko_get_pty(self):
        skip()

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
