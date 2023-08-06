"""
Tests testing the publicly exposed test helper API.

Most of the testing module is tested via use in our own test suite, but
considering it's publicly-exposed code, we should have some dedicated tests to
it!

And thank goodness we're not using vanilla unittest/pytest or the word "test"
would be in here more than you can shake a buffalo at (see:
https://en.wikipedia.org/wiki/Buffalo_buffalo_Buffalo_buffalo_buffalo_buffalo_Buffalo_buffalo)
"""

from unittest.mock import Mock

from fabric import Connection
from fabric.testing.base import MockRemote
from pytest import raises


class MockRemote_:
    class contextmanager_behavior:
        def calls_safety_and_stop_on_exit_with_try_finally(self):
            mr = MockRemote()
            # Stop now, before we overwrite, lest we leak the automatic mocking
            # from init time.
            mr.stop()
            mr.stop = Mock()
            mr.safety = Mock(side_effect=Exception("onoz"))
            with raises(Exception, match="onoz"):
                with mr:
                    pass
            # assert exit behavior
            mr.safety.assert_called_once_with()
            mr.stop.assert_called_once_with()

    class enable_sftp:
        def does_not_break_ssh_mocking(self):
            with MockRemote(enable_sftp=True) as mr:
                mr.expect(cmd="whoami")
                cxn = Connection(host="whatevs")
                cxn.run("whoami", in_stream=False)
                # Safety: can call sftp stuff w/o expect()ing it, should noop
                # instead of exploding
                cxn.put("whatevs")

        def enables_per_session_sftp_mocks(self):
            with MockRemote(enable_sftp=True) as mr:
                mr.expect(
                    cmd="rm file",
                    transfers=[
                        dict(
                            method="put",
                            localpath="/local/whatevs",
                            remotepath="/remote/whatevs",
                        )
                    ],
                )
                cxn = Connection(host="host")
                cxn.run("rm file", in_stream=False)
                cxn.put("whatevs")

        def safety_checks_work(self):
            with raises(AssertionError, match=r"put(.*whatevs)"):
                with MockRemote(enable_sftp=True) as mr:
                    mr.expect(
                        transfers=[
                            dict(
                                method="put",
                                localpath="/local/whatevs",
                                remotepath="/remote/whatevs",
                            )
                        ],
                    )
                    cxn = Connection(host="host")
                    # Satisfy the less rigorous default expectations for
                    # commands
                    cxn.run("rm file", in_stream=False)
                    # Oh no! The wrong put()!
                    cxn.put("onoz")
