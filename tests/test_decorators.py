from nose.tools import eq_
from fudge import Fake, with_fakes

from fabric import decorators


def fake_function(*args, **kwargs):
    """
    Returns a ``fudge.Fake`` exhibiting function-like attributes.

    Passes in all args/kwargs to the ``fudge.Fake`` constructor. However, if
    ``callable`` or ``expect_call`` kwargs are not given, ``callable`` will be
    set to True by default.
    """
    # Must define __name__ to be compatible with function wrapping mechanisms
    # like @wraps().
    if 'callable' not in kwargs and 'expect_call' not in kwargs:
        kwargs['callable'] = True
    return Fake(*args, **kwargs).has_attr(__name__='fake')


@with_fakes
def test_runs_once_runs_only_once():
    """
    @runs_once prevents decorated func from running >1 time
    """
    func = fake_function(expect_call=True).times_called(1)
    task = decorators.runs_once(func)
    for i in range(2):
        task()


def test_runs_once_returns_same_value_each_run():
    """
    @runs_once memoizes return value of decorated func
    """
    return_value = "foo"
    task = decorators.runs_once(fake_function().returns(return_value))
    for i in range(2):
        eq_(task(), return_value)
