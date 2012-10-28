from fabric import tasks

class ClassBasedTask(tasks.Task):
    def run(self, *args, **kwargs):
        pass

foo = ClassBasedTask()
