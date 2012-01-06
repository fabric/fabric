from nose.tools import eq_

from fabric.state import AliasDict


def test_dict_aliasing():
    """
    Assigning values to aliases updates aliased keys
    """
    ad = AliasDict(
        {'bar': False, 'biz': True, 'baz': False,
         'foo': ['bar', 'biz', 'baz']}
    )
    # Before
    eq_(ad['bar'], False)
    eq_(ad['biz'], True)
    eq_(ad['baz'], False)
    # Change
    ad['foo'] = True
    # After
    eq_(ad['bar'], True)
    eq_(ad['biz'], True)
    eq_(ad['baz'], True)


def test_nested_dict_aliasing():
    """
    Aliases can be nested
    """
    ad = AliasDict(
        {'bar': False, 'biz': True, 'foo': ['bar', 'nested'],
         'nested': ['biz']}
    )
    # Before
    eq_(ad['bar'], False)
    eq_(ad['biz'], True)
    # Change
    ad['foo'] = True
    # After
    eq_(ad['bar'], True)
    eq_(ad['biz'], True)


def test_dict_alias_expansion():
    """
    Alias expansion
    """
    ad = AliasDict(
        {'bar': False, 'biz': True, 'foo': ['bar', 'nested'],
         'nested': ['biz']}
    )
    eq_(ad.expand_aliases(['foo']), ['bar', 'biz'])
