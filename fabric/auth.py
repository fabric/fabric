"""
Common authentication subroutines. Primarily for internal use.
"""


def get_password():
    from fabric.state import env
    return env.passwords.get(env.host_string, env.password)

def set_password(password):
    from fabric.state import env
    if not env.password:
        env.password = password
    if not env.passwords.get(env.host_string):
        env.passwords[env.host_string] = password
