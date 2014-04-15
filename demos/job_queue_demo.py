from fabric.job_queue import JobQueue
from multiprocessing import Process as Bucket
from multiprocessing import Queue

def main():
    """
    This will run the queue through it's paces, and show a simple way of using
    the job queue.
    """

    def print_number(number):
        """
        Simple function to give a simple task to execute.
        """
        print(number)

    queue = Queue()
    # Make a job_queue with a bubble of len 5, and have it print verbosely
    jobs = JobQueue(5, queue)
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
    main()
