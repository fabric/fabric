from fabric.api import env


class Integration(object):
    def setup(self):
        env.host_string = "127.0.0.1"
