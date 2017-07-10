from pytest import fixture

from ._util import MockRemote


@fixture
def remote():
    """
    Fixture allowing setup of a mocked remote session & access to sub-mocks.

    Yields a `MockRemote` object (which may need to be updated via
    `MockRemote.expect`, `MockRemote.expect_sessions`, etc; otherwise a default
    session will be used) & calls `MockRemote.stop` on teardown.
    """
    remote = MockRemote()
    yield remote
    remote.stop()
