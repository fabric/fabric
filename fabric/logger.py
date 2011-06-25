import logging


class FabricLogRecord(logging.LogRecord):
    def __init__(self, name, level, pathname, lineno, msg, args, exc_info,
            func=None, extras=None):
        if extras and "show_prefix" in extras:
            self.show_prefix = extras["show_prefix"]
            del extras["show_prefix"]

        super(FabricLogRecord, self).__init__(name, level, pathname,
                lineno, msg, args, exc_info, func=func)

        from fabric.state import env
        self.__dict__["host"] = env.host_string


class FabricLogger(logging.getLoggerClass()):
    def __init__(self, name):
        super(FabricLogger, self).__init__(name)

    def makeRecord(self, *args, **kwargs):
        return FabricLogRecord(*args, **kwargs)


logging.setLoggerClass(FabricLogger)
log = logging.getLogger("fabric")
system_log = logging.getLogger("fabric-system")

class FabricFormatter(logging.Formatter):
    def __init__(self, format, prefix=None, *args, **kwargs):
        self.prefix = prefix
        super(FabricFormatter, self).__init__(format, *args, **kwargs)

    def format(self, record):
        orig_format = False
        from fabric.state import env
        if self.prefix and getattr(record, "show_prefix", env.output_prefix):
            format = "%s %s" % (self.prefix, self._fmt)
            orig_format = self._fmt
            self._fmt = format
        ret = super(FabricFormatter, self).format(record)
        if orig_format:
            self._fmt = orig_format
        return ret


def configure_system_logging(level=logging.INFO):
    formatter = logging.Formatter("%(message)s")
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    system_log.addHandler(console)
    system_log.setLevel(level)


def configure_fabric_logging(level=logging.INFO):
    formatter = FabricFormatter("%(message)s", prefix="[%(host)s]")
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    log.addHandler(console)
    log.setLevel(level)


# TODO: make sure regular handler doesn't dupe error handler
# TODO: add a ColorFormatter
def configure_logging(level=logging.INFO):
    configure_system_logging(level)
    configure_fabric_logging(level)
