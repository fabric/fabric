from fabric.api import env


class Integration(object):
    def setup(self):
        # Just so subclasses can super() us w/o fear. Meh.
        pass

    def teardown(self):
        # Just so subclasses can super() us w/o fear. Meh.
        pass
