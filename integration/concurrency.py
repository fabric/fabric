import codecs

from invoke.vendor.six.moves.queue import Queue
from random import randint
from threading import Thread

from spec import Spec, ok_, eq_

from fabric import Connection


class concurrency(Spec):
    # TODO: still useful to use Group API here? Where does this responsibility
    # fall between Group and Executor (e.g. phrasing this specifically as a
    # generic subcase of Invoke level task parameterization)?

    # TODO: spin up multiple temp SSHDs / Paramiko servers / ???

    def setup(self):
        cxn1 = Connection('localhost')
        cxn2 = Connection('localhost')
        cxn3 = Connection('localhost')
        self.cxns = (cxn1, cxn2, cxn3)

    def connections_objects_do_not_share_connection_state(self):
        cxn1, cxn2, cxn3 = self.cxns
        [x.open() for x in self.cxns]
        # Prove no exterior connection caching, socket reuse, etc
        # NOTE: would phrase these as chained 'is not' but pep8 linter is being
        # stupid :(
        ok_(cxn1 is not cxn2)
        ok_(cxn2 is not cxn3)
        ok_(cxn1.client is not cxn2.client)
        ok_(cxn2.client is not cxn3.client)
        ports = [x.transport.sock.getsockname()[1] for x in self.cxns]
        ok_(ports[0] is not ports[1] is not ports[2])

    def manual_threading_works_okay(self):
        # Kind of silly but a nice base case for "how would someone thread this
        # stuff; and are there any bizarre gotchas lurking in default
        # config/context/connection state?"
        queue = Queue()
        def worker(cxn, queue):
            # Use large random slice of words dict as a crummy "make sure
            # each thread isn't polluting things like stored stdout" sanity
            # test
            # TODO: skip test on Windows or find suitable alternative file
            words = '/usr/share/dict/words'
            with codecs.open(words, encoding='utf-8') as fd:
                data = [x.strip() for x in fd.readlines()]
            num_words = len(data)
            # Arbitrary size - it's large enough to _maybe_ catch issues,
            # but small enough that the chance of each thread getting a
            # different chunk is high
            # EDIT: was using 100k on OS X but dict on Travis' Trusty builds is
            # only 99k in total, so...ugh. 15k it is.
            window_size = 15000
            err = "Dict size only {0} words!".format(num_words)
            assert num_words > window_size, err
            start = randint(0, (num_words - window_size - 1))
            end = start + window_size
            tail = num_words - start
            expected = data[start:end]
            cmd = "tail -n {} {} | head -n {}".format(
                tail, words, window_size,
            )
            stdout = cxn.run(cmd, hide=True).stdout
            result = [x.strip() for x in stdout.splitlines()]
            queue.put((result, expected))
        kwargs = dict(queue=queue)
        threads = [
            Thread(target=worker, kwargs=dict(kwargs, cxn=cxn))
            for cxn in self.cxns
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(5) # Kinda slow, but hey, maybe the test runner is hot
        while not queue.empty():
            result, expected = queue.get(block=False)
            eq_(result, expected)
