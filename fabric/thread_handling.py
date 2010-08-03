import threading


class ThreadHandler(object):
    def __init__(self, name, callable, *args, **kwargs):
        self.exception = None
        def wrapper(*args, **kwargs):
            try:
                callable(*args, **kwargs)
            except BaseException, e:
                self.exception = e
        thread = threading.Thread(None, wrapper, name, args, kwargs)
        thread.setDaemon(True)
        thread.start()
        self.thread = thread

    def join(self):
        self.thread.join()
        if self.exception is not None:
            print("##### Raising stored exception")
            raise self.exception
