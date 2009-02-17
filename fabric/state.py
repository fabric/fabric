"""
Internal shared-state variables such as config settings and host lists.
"""


class AttributeDict(dict):
    """
    Dictionary subclass enabling attribute lookup/assignment of keys/values.

    For example:

        >>> m = AttributeDict({'foo': 'bar'})
        >>> m.foo
        bar
        >>> m.foo = 'not bar'
        >>> m['foo']
        not bar

    AttributeDict objects also provide .first() which acts like .get() but
    accepts multiple keys as arguments, and returns the value of the first hit,
    e.g.

        >>> m = AttributeDict({'foo': 'bar', 'biz': 'baz'})
        >>> m.first('wrong', 'incorrect', 'foo', 'biz')
        bar

    """
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    def first(self, *names):
        for name in names:
            value = self.get(name)
            if value:
                return value


# Global environment dict. Currently a catchall for everything: config settings
# such as global deep/broad mode, host lists, username etc.
env = AttributeDict({
    'version': '0.1.0',
    'settings_file': '~/.fabrc',
})
