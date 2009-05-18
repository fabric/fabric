from nose.tools import eq_

from fabric.state import _AliasDict


def test_dict_aliasing():
    """
    Assigning values to aliases updates aliased keys
    """
    ad = _AliasDict(
        {'bar': False, 'biz': True, 'baz': False},    
        aliases={'foo': ['bar', 'biz', 'baz']}
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


def test_dict_nested_aliasing():
    """
    Aliases can be nested
    """
    ad = _AliasDict(
        {'bar': False, 'biz': True},    
        aliases={'foo': ['bar', 'nested'], 'nested': ['biz']}
    )
    # Before
    eq_(ad['bar'], False)
    eq_(ad['biz'], True)
    # Change
    ad['foo'] = True
    # After
    eq_(ad['bar'], True)
    eq_(ad['biz'], True)
