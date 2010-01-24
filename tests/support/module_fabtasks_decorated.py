from fabric.decorators import task
FABRIC_TASK_MODULE = True

@task
def hello():
    print "hello"

def world():
    print "world"
