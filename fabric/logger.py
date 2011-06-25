import logging


class Proxy(object):
    def __init__(self, wraps):
        self.wraps = wraps

    def __call__(self, msg, host=None, *args, **kwargs):
        if not "extra" in kwargs:
            kwargs["extra"] = {}
        if host:
            msg = "[%s] %s" % (host, msg)
            kwargs["extra"]["host"] = host
        self.wraps(msg, *args, **kwargs)


class Logger(object):
    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger("fabric")
        self.prefix = None

    def __getattr__(self, name):
        attr = getattr(self.log, name)
        if name in ["debug", "info", "warn", "error"]:
            return Proxy(attr)
        return attr

log = Logger()


def activate_console_logging(level=logging.INFO):
    formatter = logging.Formatter("%(message)s")
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    log.addHandler(console)
    log.setLevel(level)
