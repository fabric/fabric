class Host(object):
    """
    A remote host.
    """
    def __init__(self, name=None, aliases=None):
        self.name = name
        self.aliases = aliases or []
