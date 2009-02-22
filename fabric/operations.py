"""
Functions to be used in fabfiles and other non-core code, such as run()/sudo().
"""

from state import env
from utils import abort, indent


def require(*keys, **kwargs):
    """
    Check for given keys in the shared environment dict and abort if not found.

    Positional arguments should be strings signifying what env vars should be
    checked for. If any of the given arguments do not exist, Fabric will abort
    execution and print the names of the missing keys.

    The optional keyword argument `used_for` may be a string, which will be
    printed in the error output to inform users why this requirement is in
    place. `used_for` is printed as part of the string "Th(is|ese) variable(s)
    (are|is) used for %s", so format it appropriately.

    The optional keyword argument `provided_by` may be a list of functions or
    function names which the user should be able to execute in order to set the
    key or keys; it will be included in the error output if requirements are
    not met.

    Note: it is assumed that the keyword arguments apply to all given keys as a
    group. If you feel the need to specify more than one `used_for`, for
    example, you should break your logic into multiple calls to `require()`.
    """
    # If all keys exist, we're good, so keep going.
    if all([x in env for x in keys]):
        return
    # Pluralization
    if len(keys) > 1:
        variable = "variables"
        used = "These variables are"
    else:
        variable = "variable"
        used = "This variable is"
    # Regardless of kwargs, print what was missing.
    msg = "the command '%s' failed because the following required environment %s were not defined:\n%s" % (env.current_command, variable, indent(keys))
    # Print used_for if given
    if 'used_for' in kwargs:
        msg += "\n\n%s used for %s" % (used, kwargs['used_for'])
    # And print provided_by if given
    if 'provided_by' in kwargs:
        funcs = kwargs['provided_by']
        # Pluralize this too
        if len(funcs) > 1:
            command = "one of the following commands"
        else:
            command = "the following command"
        to_s = lambda obj: getattr(obj, '__name__', str(obj))
        provided_by = [to_s(obj) for obj in funcs]
        msg += "\n\nTry running %s prior to this one, to fix the problem:\n%s" % (
            command,
            indent(provided_by)
        )
    abort(msg)
