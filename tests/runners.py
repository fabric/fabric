from spec import Spec, skip

from fabric.runners import Remote, RemoteSudo


class Remote_(Spec):
    # uses paramiko exec_command (mock)
    # pty requests a pty (ditto)
    # wrapper/preparation method wraps in bash, can be turned off
    # all other run() tests from fab1...
    pass


class RemoteSudo_(Spec):
    # wrapper/preparation method now adds sudo wrapper too
    # works well without bash wrapper
    # can auto-respond with password
    # prompts terminal (mock?) if no stored password
    # stored password works on per connection object basis (talks to
    # connection/context?)
    pass
