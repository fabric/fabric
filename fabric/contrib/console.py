"""
Console/terminal user interface functionality.
"""

import re
from fabric.api import prompt


def confirm(question, default='yes', key='response'):
    """
    Ask user a yes/no question and return their response as True or False.

    ``question`` should be a simple, grammatically complete question such as
    "Do you wish to continue?". An indicator for the default value will be
    appended automatically. This function will *not* append a question mark for
    you.

    By default, when the user presses Enter without typing anything, "yes" is
    assumed. This can be changed by specifying ``default='no'``.
    """
    input_res = prompt(question,
                       key=key,
                       default=default,
                       validate=r'^(?i)(y(yes)?|no?)$').lower()

    return re.match('^(?i)y(es)?$', input_res)
