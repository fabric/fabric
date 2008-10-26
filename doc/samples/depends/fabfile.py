
# Illustrates how the `invoke()` operation is broken.
config.fab_hosts=['localhost']
def a():
    run("echo a")

# Works:
@depends(a)
def b1():
    run("echo b1")

# Broken, a() called twice, no b2:
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

# Semi-works, b2 still breaks:
@depends(b2)
def c12():
    run("echo c12")

# Works:
@depends(b3)
def c13():
    run("echo c13")

# Broken, a() called twice, no c21:
def c21():
    invoke(b1)
    run("echo c21")

# Totally broken, a() called thrice:
def c22():
    invoke(b2)
    run("echo c22")

# Broken, a() called twice, no c23:
def c23():
    invoke(b3)
    run("echo c23")

# Broken, a() not called:
def c31():
    b1()
    run("echo c31")

# Broken, a() called twice, then stops:
def c32():
    b2()
    run("echo c32")

# Works:
def c33():
    b3()
    run("echo c33")
