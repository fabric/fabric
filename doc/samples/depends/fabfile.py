
# Illustrates how the `invoke()` operation is broken.
config.fab_hosts=['localhost']
def a():
    run("echo a")

# Works:
@depends(a)
def b1():
    run("echo b1")

# Works:
def b2():
    invoke(a)
    run("echo b2")

# Works:
def b3():
    a()
    run("echo b3")

# Works:
@depends(b1)
def c11():
    run("echo c11")

# Works:
@depends(b2)
def c12():
    run("echo c12")

# Works:
@depends(b3)
def c13():
    run("echo c13")

# Works:
def c21():
    invoke(b1)
    run("echo c21")

# Works:
def c22():
    invoke(b2)
    run("echo c22")

# Works:
def c23():
    invoke(b3)
    run("echo c23")

# Broken, a() not called:
def c31():
    b1()
    run("echo c31")

# Works:
def c32():
    b2()
    run("echo c32")

# Works:
def c33():
    b3()
    run("echo c33")
