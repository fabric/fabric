from fabric import tasks


class ClassBasedTask(tasks.Task):
    name = 'foo'

    def run(self, *args, **kwargs):
        pass

foo = ClassBasedTask()
