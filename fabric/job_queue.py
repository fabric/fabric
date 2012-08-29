"""
Sliding-window-based job/task queue class (& example of use.)

May use ``multiprocessing.Process`` or ``threading.Thread`` objects as queue
items, though within Fabric itself only ``Process`` objects are used/supported.
"""

from __future__ import with_statement
import time
import Queue

from collections import deque

from fabric.network import ssh


class JobQueue(object):
    """
    The goal of this class is to make a queue of processes to run, and go
    through them running X number at any given time.

    So if the bubble is 5 start with 5 running and move the bubble of running
    procs along the queue looking something like this:

        Start
        ...........................
        [~~~~~]....................
        ___[~~~~~].................
        _________[~~~~~]...........
        __________________[~~~~~]..
        ____________________[~~~~~]
        ___________________________
                                End
    """
    def __init__(self, max_running, comms_queue, role_limits=None, debug=False):
        """
        Setup the class to resonable defaults.
        """
        self._max = max_running
        self._comms_queue = comms_queue
        self._debug = debug

        if role_limits is None:
            role_limits = {}
        role_limits.setdefault('default', self._max)

        self._pools = {}
        for role, limit in role_limits.iteritems():
            self._pools[role] = {
                'running': [],
                'queue': deque(),
                'limit': limit,
            }

        self._completed = []
        self._num_of_jobs = 0
        self._finished = False
        self._closed = False

    def __len__(self):
        """
        Just going to use number of jobs as the JobQueue length.
        """
        return self._num_of_jobs

    def close(self):
        """
        A sanity check, so that the need to care about new jobs being added in
        the last throws of the job_queue's run are negated.
        """
        if self._debug:
            print("JOB QUEUE: closed")

        self._closed = True

    def append(self, process):
        """
        Add the Process() to the queue, so that later it can be checked up on.
        That is if the JobQueue is still open.

        If the queue is closed, this will just silently do nothing.

        To get data back out of this process, give ``process`` access to a
        ``multiprocessing.Queue`` object, and give it here as ``queue``. Then
        ``JobQueue.run`` will include the queue's contents in its return value.
        """
        if not self._closed:
            r = process.name.split('|')[0]
            role = r if r in self._pools else 'default'

            self._pools[role]['queue'].appendleft(process)

            self._num_of_jobs += 1
            if self._debug:
                print("JOB QUEUE: %s: added %s" % (role, process.name))

    def run(self):
        """
        This is the workhorse. It will take the intial jobs from the _queue,
        start them, add them to _running, and then go into the main running
        loop.

        This loop will check for done procs, if found, move them out of
        _running into _completed. It also checks for a _running queue with open
        spots, which it will then fill as discovered.

        To end the loop, there have to be no running procs, and no more procs
        to be run in the queue.

        This function returns an iterable of all its children's exit codes.
        """
        if not self._closed:
            raise Exception("Need to close() before starting.")

        if self._debug:
            print("JOB QUEUE: starting")

        def _consume_result(comms_queue, results, ignore_empty=False):
            """
            Helper function to attempt to get results from the comms queue
            and put them into the results dict
            """
            try:
                datum = self._comms_queue.get_nowait()
            except Queue.Empty:
                if not ignore_empty:
                    raise
            else:
                results[datum['name']]['result'] = datum['result']

        results = {}

        while len(self._completed) < self._num_of_jobs:
            for pool_name, pool in self._pools.iteritems():
                while len(pool['queue']) and len(pool['running']) < pool['limit']:
                    job = pool['queue'].pop()
                    if self._debug:
                        print("JOB QUEUE: %s: %s: start" % (pool_name, job.name))
                    job.start()
                    pool['running'].append(job)

                    # job.name contains role so split that off and discard
                    host_string = job.name.split('|')[-1]
                    # Place holder for when the job finishes
                    results[host_string] = {
                        'exit_code': None,
                        'result': None
                    }

                for i, job in enumerate(pool['running']):
                    if not job.is_alive():
                        if self._debug:
                            print("JOB QUEUE: %s: %s: finish" % (pool_name, job.name))

                        job.join()  # not necessary for Process but is for Thread
                        self._completed.append(job)
                        pool['running'].pop(i)

                        host_string = job.name.split('|')[-1]
                        results[host_string]['exit_code'] = job.exitcode

                        # Let's consume a result so the queue doesn't get big
                        _consume_result(self._comms_queue, results, True)

                if self._debug:
                    print("JOB QUEUE: %s: %d running jobs" % (pool_name, len(pool['running'])))

                    if len(pool['queue']) == 0:
                        print("JOB QUEUE: %s: depleted" % pool_name)

            # Allow some context switching
            time.sleep(ssh.io_sleep)

        # Make sure to drain the comms queue since all jobs are completed
        while True:
            try:
                _consume_result(self._comms_queue, results)
            except Queue.Empty:
                break

        return results


#### Sample

def try_using(parallel_type):
    """
    This will run the queue through it's paces, and show a simple way of using
    the job queue.
    """

    def print_number(number):
        """
        Simple function to give a simple task to execute.
        """
        print(number)

    if parallel_type == "multiprocessing":
        from multiprocessing import Process as Bucket  # noqa

    elif parallel_type == "threading":
        from threading import Thread as Bucket  # noqa

    # Make a job_queue with a bubble of len 5, and have it print verbosely
    jobs = JobQueue(5)
    jobs._debug = True

    # Add 20 procs onto the stack
    for x in range(20):
        jobs.append(Bucket(
            target=print_number,
            args=[x],
            kwargs={},
        ))

    # Close up the queue and then start it's execution
    jobs.close()
    jobs.run()


if __name__ == '__main__':
    try_using("multiprocessing")
    try_using("threading")
