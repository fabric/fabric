from os.path import isfile, expanduser

from pytest import fixture

from fabric import Connection
from fabric.transfer import Transfer
from mock import Mock, patch

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
    transfer = Transfer(Connection("host"))
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


@fixture
def client():
    """
    Yields a mocked-out SSHClient for testing calls to connect() & co.

    It updates get_transport to return a mock that appears active on first
    check, then inactive after, matching most tests' needs by default:

    - `Connection` instantiates, with a None ``.transport``.
    - Calls to ``.open()`` test ``.is_connected``, which returns ``False`` when
      ``.transport`` is falsey, and so the first open will call
      ``SSHClient.connect`` regardless.
    - ``.open()`` then sets ``.transport`` to ``SSHClient.get_transport()``, so
      ``Connection.transport`` is effectively
      ``client.get_transport.return_value``.
    - Subsequent activity will want to think the mocked SSHClient is
      "connected", meaning we want the mocked transport's ``.active`` to be
      ``True``.
    - This includes ``Connection.close``, which short-circuits if
      ``.is_connected``; having a statically ``True`` active flag means a full
      open -> close cycle will run without error. (Only tests that double-close
      or double-open should have issues here.)

    End result is that:

    - ``.is_connected`` behaves False after instantiation and before ``.open``,
      then True after ``.open``
    - ``.close`` will work normally on 1st call
    - ``.close will behave "incorrectly" on subsequent calls (since it'll think
      connection is still live.) Tests that check the idempotency of ``.close``
      will need to tweak their mock mid-test.

    For 'full' fake remote session interaction (i.e. stdout/err
    reading/writing, channel opens, etc) see `remote`.
    """
    with patch("fabric.connection.SSHClient") as SSHClient:
        client = SSHClient.return_value
        client.get_transport.return_value = Mock(active=True)
        yield client


@fixture(autouse=True)
def no_user_ssh_config():
    """
    Cowardly refuse to ever load what looks like user SSH config paths.

    Prevents the invoking user's real config from gumming up test results or
    inflating test runtime (eg if it sets canonicalization on, which will incur
    DNS lookups for nearly all of this suite's bogus names).
    """
    # An ugly, but effective, hack. I am not proud. I also don't see anything
    # that's >= as bulletproof and less ugly?
    # TODO: ideally this should expand to cover system config paths too, but
    # that's even less likely to be an issue.
    def no_config_for_you(path):
        if path == expanduser("~/.ssh/config"):
            return False
        return isfile(path)

    with patch("fabric.config.os.path.isfile", no_config_for_you):
        yield
