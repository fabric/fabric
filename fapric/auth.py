"""
Common authentication subroutines. Primarily for internal use.
"""


def get_password():
    from fapric.state import env
    return env.passwords.get(env.host_string, env.password)


def set_password(password):
    from fapric.state import env
    env.password = env.passwords[env.host_string] = password
