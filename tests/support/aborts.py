from fabric.api import task, abort

@task
def kaboom():
    abort("It burns!")
