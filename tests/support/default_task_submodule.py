from swatch.api import task

@task(default=True)
def long_task_name():
    pass
