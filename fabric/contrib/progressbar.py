import sys
from fabric.colors import *

def show_progressbar(another_callback=None, progress_char='#', progress_color_function=green, file_name_color_function=blue, show_percents=True, percents_color_function=yellow):
    """
    Function returns a progressbar callback that can be used 
    as a 'callback' argument for get/put operation.

    `another_callback` is an argument that makes possible the 
    callback chaining.

    `show_percents` makes the progressbar show the percent 
    progress at the end of line.
    """
    number_of_columns = _get_terminal_size()[0] # for some reason the size of console is over by one
    is_already_finished = [False]
    def show_progressbar_on_terminal(file_name, size_so_far, overall_size):
        file_name_len = len(file_name)

        if not is_already_finished[0]:
            fraction_done = float(size_so_far)/overall_size
            progressbar_len = int(fraction_done*number_of_columns)

            def progressbar_with_filename():
                show_file_name_after_progressbar = file_name_len + 1 > progressbar_len
                if show_file_name_after_progressbar:
                    progress_to_show = progress_color_function(progress_char*progressbar_len) + ' ' + file_name_color_function(file_name)
                    number_of_columns = progressbar_len + file_name_len + 1
                else:
                    progress_to_show = file_name_color_function(file_name) + ' ' + progress_color_function(progress_char*(progressbar_len - file_name_len - 1))
                    number_of_columns = progressbar_len

                return (progress_to_show, number_of_columns)

            def progressbar_without_filename():
                return (progress_color_function(progress_char*progressbar_len), progressbar_len)

            can_show_file_name = file_name_len + progressbar_len + 1 < number_of_columns 
            if can_show_file_name:
                (progressbar, number_of_columns_taken) = progressbar_with_filename()
            else:
                (progressbar, number_of_columns_taken) = progressbar_without_filename()

            if show_percents:
                percents_string = "%.2f%%" % (fraction_done*100)
                percents_len = len(percents_string)
                number_of_spaces_before_percents = number_of_columns - number_of_columns_taken - percents_len
                if (number_of_spaces_before_percents > 0):
                    progressbar += (' '*number_of_spaces_before_percents) + percents_color_function(percents_string)

            if size_so_far == overall_size:
                progressbar += '\n'
                is_already_finished[0] = True

            sys.stdout.write('\r' + progressbar)
            sys.stdout.flush()
        elif size_so_far != overall_size:
            is_already_finished[0] = False
            show_progressbar_on_terminal(file_name, size_so_far, overall_size)

    def progressbar_callback(file_name, size_so_far, overall_size):
        show_progressbar_on_terminal(file_name, size_so_far, overall_size)
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


