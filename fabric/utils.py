import os
import sys


win32 = (sys.platform == 'win32')


def get_local_user():
    """
    Return the local executing username, or ``None`` if one can't be found.
    """
    # FIXME: I don't understand why these lines were added outside the
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
    except ImportError:
        if win32:
            import win32api
            import win32security # noqa
            import win32profile # noqa
            username = win32api.GetUserName()
    return username


def isatty(stream):
    """
    Check if a stream is a tty.

    Not all file-like objects implement the `isatty` method.
    """
    fn = getattr(stream, 'isatty', None)
    if fn is None:
        return False
    return fn()


def get_pty_size():
    """
    Obtain (cols, rows) tuple for sizing a pty on the remote end.

    Defaults to 80x24 but will try to detect local (stdout-based) terminal
    window size on non-Windows platforms.
    """
    if not win32:
        import fcntl
        import termios
        import struct

    default_cols, default_rows = 80, 24
    cols, rows = default_cols, default_rows
    if not win32 and isatty(sys.stdout):
        # We want two short unsigned integers (rows, cols)
        fmt = 'HH'
        # Create an empty (zeroed) buffer for ioctl to map onto. Yay for C!
        buffer = struct.pack(fmt, 0, 0)
        # Call TIOCGWINSZ to get window size of stdout, returns our filled
        # buffer
        try:
            result = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ,
                buffer)
            # Unpack buffer back into Python data types. (Note: WINSZ gives us
            # rows-by-cols, instead of cols-by-rows.)
            rows, cols = struct.unpack(fmt, result)
            # Fall back to defaults if TIOCGWINSZ returns unreasonable values
            if rows == 0:
                rows = default_rows
            if cols == 0:
                cols = default_cols
        # Deal with e.g. sys.stdout being monkeypatched, such as in testing.
        # Or termios not having a TIOCGWINSZ.
        except AttributeError:
            pass
    return cols, rows
