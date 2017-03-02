from invoke.vendor.six.moves.queue import Queue
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
        ok_(cxn1 is not cxn2 is not cxn3)
        ok_(cxn1.client is not cxn2.client is not cxn3.client)
        ports = [x.transport.sock.getsockname()[1] for x in self.cxns]
        ok_(ports[0] is not ports[1] is not ports[2])

    def manual_threading_works_okay(self):
        # Kind of silly but a nice base case for "how would someone thread this
        # stuff; and are there any bizarre gotchas lurking in default
        # config/context/connection state?"
        queue = Queue()
        def make_worker(index):
            cxn = self.cxns[index]
            # TODO: grab a random, idk, 10k lines from /usr/share/dict/words
            # instead? Much more opportunity for threading shenanigans that way
            cmd = 'echo {}'.format(index + 1)
            def worker():
                queue.put(cxn.run(cmd, hide=True))
            return worker
        t1 = Thread(target=make_worker(0))
        t2 = Thread(target=make_worker(1))
        t3 = Thread(target=make_worker(2))
        threads = (t1, t2, t3)
        for t in threads:
            t.start()
        for t in threads:
            t.join(5) # Kinda slow, but hey, maybe the test runner is hot
        results = []
        while not queue.empty():
            results.append(queue.get(block=False))
        # Not really sure what a failure would look like, but let's say
        # something getting real gummed up and two sessions getting the same
        # command to be run, output from one appearing in another, etc?
        outs = sorted(x.stdout.strip() for x in results)
        eq_(outs, [u'1', u'2', u'3'])
