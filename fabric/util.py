import sys


win32 = (sys.platform == 'win32')


def get_local_user():
    """
    Return the local executing username, or ``None`` if one can't be found.
    """
    # TODO: I don't understand why these lines were added outside the
    # try/except, since presumably it means the attempt at catching ImportError
    # wouldn't work. However, that's how the contributing user committed it.
    # Need an older Windows box to test it out, most likely.
    import getpass
    username = None
    # All Unix and most Windows systems support the getpass module.
    try:
        username = getpass.getuser()
    # Some SaaS platforms raise KeyError, implying there is no real user
    # involved. They get the default value of None.
    except KeyError:
        pass
    # Older (?) Windows systems don't support getpass well; they should
    # have the `win32` module instead.
    except ImportError: # pragma: nocover
        if win32:
            import win32api
            import win32security # noqa
            import win32profile # noqa
            username = win32api.GetUserName()
    return username
