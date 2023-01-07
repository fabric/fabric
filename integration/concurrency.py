import codecs
from itertools import zip_longest
from queue import Queue

from invoke.util import ExceptionHandlingThread
from pytest import skip

from fabric import Connection


_words = "/usr/share/dict/words"


def _worker(queue, cxn, start, num_words, count, expected):
    tail = num_words - start
    cmd = "tail -n {} {} | head -n {}".format(tail, _words, count)
    stdout = cxn.run(cmd, hide=True).stdout
    result = [x.strip() for x in stdout.splitlines()]
    queue.put((cxn, result, expected))


class concurrency:
    # TODO: still useful to use Group API here? Where does this responsibility
    # fall between Group and Executor (e.g. phrasing this specifically as a
    # generic subcase of Invoke level task parameterization)?

    # TODO: spin up multiple temp SSHDs / Paramiko servers / ???

    def setup(self):
        cxn1 = Connection("localhost")
        cxn2 = Connection("localhost")
        cxn3 = Connection("localhost")
        self.cxns = (cxn1, cxn2, cxn3)

    def connections_objects_do_not_share_connection_state(self):
        cxn1, cxn2, cxn3 = self.cxns
        [x.open() for x in self.cxns]
        # Prove no exterior connection caching, socket reuse, etc
        # NOTE: would phrase these as chained 'is not' but pep8 linter is being
        # stupid :(
        assert cxn1 is not cxn2
        assert cxn2 is not cxn3
        assert cxn1.client is not cxn2.client
        assert cxn2.client is not cxn3.client
        ports = [x.transport.sock.getsockname()[1] for x in self.cxns]
        assert ports[0] is not ports[1] is not ports[2]

    def manual_threading_works_okay(self):
        # TODO: needs https://github.com/pyinvoke/invoke/issues/438 fixed
        # before it will reliably pass
        skip()
        # Kind of silly but a nice base case for "how would someone thread this
        # stuff; and are there any bizarre gotchas lurking in default
        # config/context/connection state?"
        # Specifically, cut up the local (usually 100k's long) words dict into
        # per-thread chunks, then read those chunks via shell command, as a
        # crummy "make sure each thread isn't polluting things like stored
        # stdout" sanity test
        queue = Queue()
        # TODO: skip test on Windows or find suitable alternative file
        with codecs.open(_words, encoding="utf-8") as fd:
            data = [x.strip() for x in fd.readlines()]
        threads = []
        num_words = len(data)
        chunksize = len(data) / len(self.cxns)  # will be an int, which is fine
        for i, cxn in enumerate(self.cxns):
            start = i * chunksize
            end = max([start + chunksize, num_words])
            chunk = data[start:end]
            kwargs = dict(
                queue=queue,
                cxn=cxn,
                start=start,
                num_words=num_words,
                count=len(chunk),
                expected=chunk,
            )
            thread = ExceptionHandlingThread(target=_worker, kwargs=kwargs)
            threads.append(thread)
        for t in threads:
            t.start()
        for t in threads:
            t.join(5)  # Kinda slow, but hey, maybe the test runner is hot
        while not queue.empty():
            cxn, result, expected = queue.get(block=False)
            for resultword, expectedword in zip_longest(result, expected):
                err = "({2!r}, {3!r}->{4!r}) {0!r} != {1!r}".format(
                    resultword, expectedword, cxn, expected[0], expected[-1]
                )
                assert resultword == expectedword, err
