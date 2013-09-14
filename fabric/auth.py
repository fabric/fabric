"""
Common authentication subroutines. Primarily for internal use.
"""
import state
import network


def get_password(user, host, port):
    host_string = network.join_host_strings(user, host, port)
    return state.env.passwords.get(host_string, state.env.password)


def set_password(user, host, port, password):
    host_string = network.join_host_strings(user, host, port)
    state.env.password = state.env.passwords[host_string] = password
