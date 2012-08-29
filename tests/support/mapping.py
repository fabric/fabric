from fabric.tasks import Task


class MappingTask(Task, dict):
    def __init__(self, *args, **kwargs):
        super(MappingTask, self).__init__(*args, **kwargs)

    def run(self):
        pass

mapping_task = MappingTask(name='mapping_task')
