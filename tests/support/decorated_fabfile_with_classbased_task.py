from fabric import tasks
from fabric.decorators import task

class ClassBasedTask(tasks.Task):
    def __init__(self):
        self.name = "foo"
        self.use_decorated = True

    def run(self, *args, **kwargs):
        pass

foo = ClassBasedTask()
