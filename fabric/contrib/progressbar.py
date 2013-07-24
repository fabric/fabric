import sys
from fabric.colors import *

def show_progressbar(another_callback=None, progress_char='#', progress_color_function=green, show_percents=True, percents_color_function=yellow):
    number_of_columns = _get_terminal_size()[0] - 2
    def show_progressbar_on_terminal(size_so_far, overall_size):
        fraction_done = float(size_so_far)/overall_size
        number_of_columns_to_show = int(fraction_done*number_of_columns)
        print('\r' + progress_color_function(progress_char*number_of_columns_to_show)),
        if show_percents:
            percents_string = str(fraction_done*100) + '%'
            percents_len = len(percents_string)
            number_of_spaces_before_percents = number_of_columns - number_of_columns_to_show - percents_len - 1
            if (number_of_spaces_before_percents > 0):
                print(' '*number_of_spaces_before_percents),
                print(percents_color_function(percents_string)),
            
        sys.stdout.flush()

    def progressbar_callback(size_so_far, overall_size):
        show_progressbar_on_terminal(size_so_far, overall_size)
        if (another_callback != None):
            another_callback(size_so_far, overall_size)

    return progressbar_callback

# Code from http://stackoverflow.com/a/566752/373671
def _get_terminal_size():
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))

        ### Use get(key[, default]) instead of a try/catch
        #try:
        #    cr = (env['LINES'], env['COLUMNS'])
        #except:
        #    cr = (25, 80)
    return int(cr[1]), int(cr[0])


