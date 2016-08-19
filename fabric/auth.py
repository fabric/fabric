"""
Common authentication subroutines. Primarily for internal use.
"""


def get_password(user, host, port, login_only=False):
    from fabric.state import env
    from fabric.network import join_host_strings
    host_string = join_host_strings(user, host, port)
    sudo_password = env.sudo_passwords.get(host_string, env.sudo_password)
    login_password = env.passwords.get(host_string, env.password)
    return login_password if login_only else sudo_password or login_password


def set_password(user, host, port, password):
    from fabric.state import env
    from fabric.network import join_host_strings
    host_string = join_host_strings(user, host, port)
    env.password = env.passwords[host_string] = password
