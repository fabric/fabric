import logging
log = logging.getLogger("fabric")
system_log = logging.getLogger("fabric-system")


def configure_system_logging(level=logging.INFO):
    formatter = logging.Formatter("%(message)s")
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    system_log.addHandler(console)
    system_log.setLevel(level)


def configure_fabric_logging(level=logging.INFO):
    formatter = logging.Formatter("[%(host)s] %(message)s")
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
