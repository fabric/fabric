from lexicon import Lexicon


class Configuration(Lexicon):
    def __init__(self, *args, **kwargs):
        super(Lexicon, self).__init__(self, *args, **kwargs)
        self.setdefault('local_user', 'bobsmith')
        self.setdefault('default_port', -200)
