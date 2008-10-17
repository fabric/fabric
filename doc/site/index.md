Fabric: simple pythonic deployment.
===================================

Fabric is a simple pythonic remote deployment tool. 

It is designed to upload files to, and run shell commands on, a number of
servers in parallel or serially. These commands are grouped in tasks (regular
python functions) and specified in a 'fabfile.'

It is a bit like a dumbed down Capistrano, except it's in Python, doesn't
expect you to be deploying Rails applications, and the 'put' command works. 

Unlike Capistrano, Fabric wants to stay small, light, easy to change and not
bound to any specific framework.

Once installed, you can run `fab help` to learn more about how to use Fabric.


Installing
----------

... is as easy as:

    $ sudo easy_install Fabric

To get the most out of Fabric, your system needs to live up to some
requirements:

 1. Python 2.5 (2.4 might work but is not tested).
 2. Python Setuptools (part of most python installations).
 3. Paramiko 1.6 or greater (requires pycrypto).
 4. A unix environment (cygwin might work but is not tested).

Fabfiles
--------

They're called 'fabfiles.' You put them in the root of your project directory,
and the filename is 'fabfile' or 'fabfile.py.' Their purpose is to describe
the commands to use and the steps to take, when you run a command with Fabric.

And, in the simplest form, they look like this:

    :::python
    set(
        project = 'awesome-app',
        fab_hosts = ['n1.cluster.com', 'n2.cluster.com'],
    )
    
    def deploy():
        "Build the project and deploy it to a specified environment."
        local('mvn package')
        put('target/$(project).war', '$(project).war')
        put('install-script.sh', 'install-script.sh')
        sudo('install-script.sh')

Then run it like this from the command line:

    $ fab deploy


License
-------

The Fabric program and scripts are released and distributed under the
[GPL v. 2 license][1].

The Fabric 'F' logo and the documentation are released under a
[Creative Commons license][2]. 

[1]: http://www.opensource.org/licenses/gpl-2.0.php
[2]: http://creativecommons.org/licenses/by-sa/2.5/dk/deed.en

