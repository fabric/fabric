from pytest import fixture

from fabric import Connection
from fabric.transfer import Transfer

from _util import MockRemote, MockSFTP


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


@fixture
def sftp():
    """
    Fixture allowing setup of a mocked remote SFTP session.

    Yields a 3-tuple of: Transfer() object, SFTP client, and mocked OS module.
    """
    mock = MockSFTP(autostart=False)
    client, mock_os = mock.start()
    transfer = Transfer(Connection('host'))
    yield transfer, client, mock_os
    # TODO: old mock_sftp() lacked any 'stop'...why? feels bad man
