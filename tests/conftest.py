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

    Yields a 3-tuple of: Transfer() object, SFTPClient object, and mocked OS
    module.

    For many/most tests which only want the Transfer and/or SFTPClient objects,
    see `sftp_objs` and `transfer` which wrap this fixture.
    """
    mock = MockSFTP(autostart=False)
    client, mock_os = mock.start()
    transfer = Transfer(Connection('host'))
    yield transfer, client, mock_os
    # TODO: old mock_sftp() lacked any 'stop'...why? feels bad man

@fixture
def sftp_objs(sftp):
    """
    Wrapper for `sftp` which only yields the Transfer and SFTPClient.
    """
    yield sftp[:2]

@fixture
def transfer(sftp):
    """
    Wrapper for `sftp` which only yields the Transfer object.
    """
    yield sftp[0]
