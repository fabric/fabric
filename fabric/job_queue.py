"""
Sliding-window-based job/task queue class (& example of use.)

May use ``multiprocessing.Process`` or ``threading.Thread`` objects as queue
items, though within Fabric itself only ``Process`` objects are used/supported.
"""

from pprint import pprint
from Crypto import Random 
import time
import Queue

from fabric.state import env
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
    def __init__(self, max_running, comms_queue):
        """
        Setup the class to resonable defaults.
        """
        self._queued = []
        self._running = []
        self._completed = []
        self._num_of_jobs = 0
        self._max = max_running
        self._comms_queue = comms_queue
        self._finished = False
        self._closed = False
        self._debug = False

    def _all_alive(self):
        """
        Simply states if all procs are alive or not. Needed to determine when
        to stop looping, and pop dead procs off and add live ones.
        """
        if self._running:
            return all([x.is_alive() for x in self._running])
        else:
            return False

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
            print("job queue closed.")

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
            self._queued.append(process)
            self._num_of_jobs += 1
            if self._debug:
                print("job queue appended %s." % process.name)

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
        def _advance_the_queue():
            """
            Helper function to do the job of poping a new proc off the queue
            start it, then add it to the running queue. This will eventually
            depleate the _queue, which is a condition of stopping the running
            while loop.

            It also sets the env.host_string from the job.name, so that fabric
            knows that this is the host to be making connections on.
            """
            job = self._queued.pop()
            if self._debug:
                print("Popping '%s' off the queue and starting it" % job.name)
            env.host_string = env.host = job.name
            job.start()
            self._running.append(job)

        if not self._closed:
            raise Exception("Need to close() before starting.")

        if self._debug:
            print("Job queue starting.")

        while len(self._running) < self._max:
            _advance_the_queue()

        while not self._finished:
            while len(self._running) < self._max and self._queued:
                _advance_the_queue()

            if not self._all_alive():
                for id, job in enumerate(self._running):
                    if not job.is_alive():
                        if self._debug:
                            print("Job queue found finished proc: %s." %
                                    job.name)
                        done = self._running.pop(id)
                        self._completed.append(done)

                if self._debug:
                    print("Job queue has %d running." % len(self._running))

            if not (self._queued or self._running):
                if self._debug:
                    print("Job queue finished.")

                for job in self._completed:
                    job.join()

                self._finished = True
            time.sleep(ssh.io_sleep)

        results = {}
        for job in self._completed:
            results[job.name] = {
                'exit_code': job.exitcode,
            }
        while True:
            try:
                datum = self._comms_queue.get(timeout=1)
                results[datum['name']]['results'] = datum['result']
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
        from multiprocessing import Process as Bucket

    elif parallel_type == "threading":
        from threading import Thread as Bucket


    # Make a job_queue with a bubble of len 5, and have it print verbosely
    jobs = JobQueue(5)
    jobs._debug = True

    # Add 20 procs onto the stack
    for x in range(20):
        jobs.append(Bucket(
            target = print_number,
            args = [x],
            kwargs = {},
            ))

    # Close up the queue and then start it's execution
    jobs.close()
    jobs.run()


if __name__ == '__main__':
    try_using("multiprocessing")
    try_using("threading")
