from spec import skip


def simple_command_on_host():
    """
    Run command on host "localhost"
    """
    Connection('localhost').run('echo foo')
    # => Result

def simple_command_on_multiple_hosts():
    """
    Run command on localhost...twice!
    """
    Batch(['localhost', 'localhost']).run('echo foo')
    # => [Result, Result

def sudo_command():
    """
    Run command via sudo on host "localhost"
    """
    Connection('localhost').sudo('echo foo')

def mixed_sudo_and_normal_commands():
    """
    Run command via sudo, and not via sudo, on "localhost"
    """
    cxn = Connection('localhost')
    cxn.run('whoami')
    cxn.sudo('whoami')
    # Alternately...
    cxn.run('whoami', runner=Basic)
    cxn.run('whoami', runner=Sudo)

def switch_command_between_local_and_remote():
    """
    Run command truly locally, and over SSH via "localhost"

    Only really makes sense at the task level though...
    """
    # Basic/raw
    run('hostname') # Or Context().run('hostname')
    Connection('localhost').run('hostname')
