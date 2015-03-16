from spec import Spec, skip

from fabric.runners import Remote, RemoteSudo


class Remote_(Spec):
    # TODO: all other run() tests from fab1...
    def uses_paramiko_exec_command(self):
        skip()

    def run_pty_uses_paramiko_get_pty(self):
        skip()

    def wraps_command_in_bash_by_default(self):
        # TODO: or should it?
        skip()

    def wrapper_subject_to_disabling(self):
        # TODO: how? also implies top level run() wants to pass **kwargs to
        # runner somehow, though that's dangerous; maybe allow runner to
        # expose what it expects so run() can correctly determine things.
        # TODO: oughtn't this be part of invoke proper?
        skip()


class RemoteSudo_(Spec):
    # wrapper/preparation method now adds sudo wrapper too
    # works well without bash wrapper
    # can auto-respond with password
    # prompts terminal (mock?) if no stored password
    # stored password works on per connection object basis (talks to
    # connection/context?)
    pass
