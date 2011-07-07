from fabric.tasks import Task

class MappingTask(dict, Task):
    def run(self):
        pass

mapping_task = MappingTask()
mapping_task.name = "mapping_task"
