User Guide
==========

Let me just first make it clear, that Fabric is alpha software and still
very much in development. So it's a moving target, documentation wise,
and it is to be expected that the information herein might not be entirely
accurate.

**Table of contents:**

{toc}

The ache
--------

Here's the thing: you're developing a server deployed application, it could
be a web application but it doesn't have to be, and you're probably
deploying to more than one server.

Even if you just have one server to deploy to, it still get tiresome in the
long run to build your project, fire up your favorite SFTP utility, upload
your build, log in to the server with SSH, possibly stop the server, deploy
the build, and finally start the server again.

What we'd like to do, is to build, upload and deploy our application with
a single command line.


Fabric: first steps
-------------------

Fabric is a tool that, at its core, logs into a number of hosts with SSH, and
executes a set of commands, and possibly uploads or downloads files.

There are two parts to it; there's the `fab` command line program, and there's
the `fabfile`. The `fabfile` is where you describe commands and what they do.
For instance, you might have a command called 'deploy' that builds, uploads
and deploys your application. The `fabfiles` are really just python scripts
and the commands are just python functions. This python script is loaded by
the `fab` program and the commands are executed as specified on the command
line.

Here's what a super simple `fabfile` might look like:

    :::python
    def hello():
        "Prints hello."
        local("echo hello")

Let's break that down line by line.

First, there's the `def hello():` line. It defines a command called `hello`
so that it can be run with `fab hello`, but we'll get to that part.

Next comes a block of text that is indented with four spaces. It is not
important that we use exactly four spaces, just that each line is consistently
indented.

The first line of the indented block is a doc-string. It documents the purpose
of the command and is used in various parts of Fabric, for instance, the
`list` command will display the first line of the doc-string next to the
name of the command in its output.

Following the doc-string is a call to a function called `local`. In Fabric
terminology, `local` is an operation. In python, functions are functions,
but Fabric distinguishes between commands and operations. Commands are called
with the `fab` command line program, and operations are in turn called by
commands. Since they're both just python functions, there's nothing stopping
commands from calling other commands as if they were operations.

Getting back to `local`, you're probably left wondering what it does. Well,
maybe you already guessed it. Regardless, there's a way to know for sure. And
that is the `help` command. A command can take parameters when run from the
command line, by appending a colon and then a parameter list to the end of the
command name. For instance, if we want to invoke the 'help' command with the
parameter `local`, we would type `fab help:local` on the command line.

Let's try doing just that:

    rowe:~$ fab help:local
    Fabric v. 0.0.9.
    Warning: Load failed:
        File not found: fabfile
    Running help...
    Help for 'local':
        Run a command locally.
        
        This operation is essentially 'os.system()' except that variables are
        expanded prior to running.
        
        May take an additional 'fail' keyword argument with one of these values:
            * ignore - do nothing on failure
            * warn - print warning on failure
            * abort - terminate fabric on failure
        
        Example:
            local("make clean dist", fail='abort')
    Done.
    rowe:~$

First, Fabric prints a header with version number &mdash; good to know.
Then, there's a warning stating that no `fabfile` was found - which is
understandable because we haven't created one yet. Finally, the `help` command
is run and it prints the built-in documentation for the `local` operation.

You can use the `list` command to figure out what other operations are
available. Try running `fab help:list` to figure out how to use it.

Since Fabric complains when it can't find any `fabfile,` let's create one.
Create a file in your current directory (of the terminal you used to run
`fab help:local` with above), call it `fabfile.py`, open it in your favorite
text editor and copy-paste the example `fabfile` above into it.

Now, let's see what happens when we run `fab hello`:

    rowe:~$ fab hello
    Fabric v. 0.0.9.
    Running hello...
    [localhost] run: echo hello
    hello
    Done.
    rowe:~$ 

Nothing in this output should come as a surprise to anyone at this point.
It does what we expect it to do. Note that Fabric makes a habit out of
printing the commands it runs, the privilege level they're run with and on
which hosts they run.


Getting connected
-----------------

We have learned how to execute shell commands on our local system with the
`local` operation. However, that in and off itself isn't particularly useful.
We can do that with shell scripts just fine. Instead, what we'd rely like to
do, is to log in to a number of remote hosts and execute the commands there.
Fabric let us do just that with these three operations:

* `put` : Uploads a file to the connected hosts.
* `run` : Run a shell-command on the connected hosts as a normal user.
* `sudo` : Run a shell-command on the connected hosts as a privileged user.

Remember that you can inspect the documentation for each of these operations
with the `help` command, ie. `fab help:put`.

These operations are the bread and butter of remote deployment in Fabric.
But before we can use them, we need to tell Fabric which hosts to connect to.
We do this by setting the `fab_hosts` attribute on the `config` object, to
a list of strings that are our host names. We can also specify the user we
want to log into these hosts with by setting the `fab_user` variable. By
default, Fabric will log in with the username of your current local user -
which is perfectly fine in this example, so we'll leave that variable out.

It is also possible to specify the username in fab_hosts, by preceding the
host name with the username and then a `@` character.

Try changing your `fabfile` so it looks like this:

    :::python
    config.fab_hosts = ['127.0.0.1']
    
    def hello():
        "Prints hello."
        local("echo hello")
    
    def hello_remote():
        "Prints hello on the remote hosts."
        run("echo hello from $(fab_host) to $(fab_user).")

We set the variables needed to connect to a host, and then we run an `echo`
command on the host. Note how we can access variables inside the string.
The dollar-parenthesis syntax is special to Fabric; it means that the variables
should be evaluated as late as possible, which in this case will be when the
`run` command actually get executed against a connected host.

Let's try running `fab hello_remote` now and see what happens:

    rowe:~$ fab hello_remote
    Fabric v. 0.0.9.
    Running hello_remote...
    Logging into the following hosts as vest:
        127.0.0.1
    Password for vest@127.0.0.1: 
    [127.0.0.1] run: echo hello from 127.0.0.1 to vest.
    [127.0.0.1] out: hello from 127.0.0.1 to vest.
    Done.
    rowe:~$ 

When we get to executing the `run` operation, the first thing that happens
is that Fabric makes sure that we are connected to our hosts, and if not,
starts connecting.


Managing multiple environments
------------------------------

We have managed to open connections to multiple hosts and execute shell
commands on them, and we know how to upload files. Basically, we have
everything we need to perform remote deployment. However, most commercial
software projects have their product move through a number of phases for
various forms of testing before the production deployment. It would be really
nice if we could have multiple environments, such as test, staging and
production, and be able to choose which environment to deploy to.

Actually, we already have all we need to do that. Consider this fabfile for
instance:

    :::python
    def test():
        config.fab_hosts = ['localhost']
    
    def staging():
        config.fab_hosts = ['n1.stg.python.org', 'n2.stg.python.org']
    
    def production():
        config.fab_hosts = ['n1.python.org', 'n2.python.org']
    
    def deploy():
        'Deploy the app to the target environment'
        local("make dist")
        put("bin/bundle.zip", "bundle.zip")
        sudo("./install.sh bundle.zip")

This way, we just need to remember to run the commands in the right order,
like `fab test deploy`. What happens if we forget to run the environment
command first? In that case Fabric will complain about the missing fab_hosts
variable with a generic error message. Not cool, plus we could picture a
complex fabfile where these environment configuration commands do other things
than setting the fab_hosts variable - we need a generic way to control the
run-order of certain commands.

This is what the `require` operation is for. It takes a name of a variable and
checks that it has been set, otherwise it will halt the execution.
Additionally, it can take a `provided_by` keyword argument with a list of those
operations that will set the said variable.

If we add a call to `require` to the beginning of our `deploy` command, we can
ensure that a proper environment will always be available:

    :::python
    def deploy():
        'Deploy the app to the target environment'
        require('fab_hosts', provided_by = [test, staging, production])
        local("make dist")
        put("bin/bundle.zip", "bundle.zip")
        sudo("./install.sh bundle.zip")

There. If we now run `deploy` with first specifying an environment, we'll be
duly told.


More on configuration
---------------------

We have seen how Fabric can connect to a set of hosts and execute an array of
commands on them. We have also touched on the built-in help system, and how we
can use it to learn more about the features that are available to us in our
fabfiles. However, to get the full potential out of Fabric, we also need to
know how to configure it.

### The `@hosts` decorator

So far, we have specified the hosts we intend to connect to, by setting the 
`config.fab_hosts` variable. When we wanted to override this setting, we always
had to define a command that proactively set that variable.

This way of re-specifying the `fab_hosts` variable doesn't really scale very
well beyond the simplest cases. As the need of switching between different set of hosts increases, it also becomes increasingly error prone to remember to run
the right set-these-hosts commands all the time.

**TBD**

### Variables

We saw in the "Getting connected" section above, that we can use a notation
such as `$(fab_user)` to interpolate the value of the `fab_user` variable in
a string. The standard python `%(fab_user)s` notation would have worked just
as well, but there are some important differences between these two notations:
The former notation is special to Fabric and is lazily evaluated, whereas the
later is a general python feature, and is eagerly evaluated.

This difference between eager and lazy evaluation is demonstrated in this
example:

    :::python
    def test():
        config.var = 'a'
        config.cmd = 'echo %(var)s $(var)'  # line 3
        config.var = 'b'
        local(config.cmd)  # line 5

If we run that as a command with Fabric, it will print out "a b". The eager
notation will be interpolated as soon as possible, which is line 3, but the
lazy notation will not be evaluated until it is actually needed, in line 5,
and by that time the value of `var` will change, resulting in the output "a b".

Having variables automatically interpolated is nice, but sometimes we don't
want it. In that case, we need to escape the interpolations and in the case of
the special `$(variable)` notation, this is easily done by preceding it with a
back-slash, like this: `\$(variable)`. The normal Python string interpolation
is escaped like it has always been; by doubling the `%` character. When we
execute commands with `local()`, `run()` and `sudo()`, the strings will pass by
bash or some other shell, who might also be eager to do interpolation of
environment variables upon seeing a `$` character. Escaping characters through
several layers of different interpolations can be tricky, but triple-back-slash
seems to work: `run("echo a string with a \\\$dollar")`.

> **Q & A: Why two different kinds of string interpolation?**
>
> The main reason for the existence of the lazy interpolation notation, is that
> some variables simply do not exist at the time that the strings are defined.
> One such variable is `fab_host` which names the actual host that an operation
> is executing on/against.
>
> Capistrano has a special string that is matched and replaced with the name of
> the current host. When creating fabric, it was decided that such a special
> string was too much of an easy-to-forget hack, and so the notion of lazy
> interpolation was created instead.

Beyond the variables you set on the `config` object, Fabric provides a
number of built-in variables. Most are for configuring Fabric itself, but some
are also for use in the string arguments you pass to `run` and `sudo` and the
like.

For a complete overview of the different variables and their use, I'm afraid
you have to consult the source code, but here's a list of the most useful ones:

* `fab_host` is available in remote operations, or other operations that take
effect on a per host basis, have access to this variable which names a
specific host to work on.
* `fab_hosts` defines the list of hosts to connect to, as a list of strings.
There's no default value for this variable so it must be specified if you
want to execute any remote operations.
* `fab_mode` specifies what strategy should be used to execute commands on the
connected hosts. The default value is "rolling" which runs the commands on one
host at a time, without any parallelism or concurrency.
* `fab_password` is the password used for logging into the remote hosts, and
to authenticate with remote `sudo` commands. Don't set this in the fabfile,
because a password-prompt will automatically ask for it when needed.
* `fab_port` is the port number used to connect to the remote hosts. The
default value is 22, which is the default SSH port number.
* `fab_user` is the username used to log in to the remote hosts with. The
default value is derived from the containing shell that executes Fabric, that
is, your currently logged in username.
* `fab_timestamp` is the UTC timestamp for when Fabric was started. Generally
useful when naming backup files or the like.

Beyond these variables, it is common practice (but not required) to set a
`project` variable to the name of your project. This variable often comes
handy in naming build-files, backup-files and deployment directories specific
to the project.

### The `config` object

**TBD**

### Key-based authentication

If you have a private key that the servers will acknowledge, then Fabric will
automatically pick it up, and if a password is required for unlocking that key,
then Fabric will ask that password. This default behavior should work for most
people, but if you use password-less keys, then note the caveat that Fabric
won't ask for a password and this in turn means that the `sudo()` operation
won't be able to parse a password to the sudo command on the remote hosts.
To counter this, you need to specify, on the remote hosts, the commands you
need for deployment as sudo'able without a password.

If you want to use a specific key file on your system, then that is possible
as well by setting the `fab_key_filename` variable to the path of your desired
key file. If you need even more control, then you can instantiate your own
[PKey][] instance and put it in the `fab_pkey` variable - this will cause it
to be parsed directly to the underlying call to [connect][] without
modification.

### User-local configurations and .fabric

In the real world (at least the part I'm in), most projects are developed in
teams. This means that more than one person might be allowed to deploy any
given project. This often means that we'll have some per-developer
configuration located on his/her computer - the *username* that is used to log
into the servers are the prime example of such individualized configuration.

This is where the .fabric file comes in; before the fabfile is loaded, Fabric
will look for a .fabric file in your home directory and load it if found.
Because it is loaded before the fabfile, you can override these defaults in the
fabfile.

The format of the .fabric file is very simple. The file is line-oriented and
every line is evaluated based on these three rules:

* Lines that are empty apart from white spaces, are ignored.
* Lines that begin with a hash `#` character, are ignored.
* Otherwise, the line must contain a variable name, followed by an equal sign
and then some text for the value - both name and value will be stripped of
leading and trailing white spaces.

An example file might look like this:

    # My default username:
    fab_user = montyp

And that's basically all there is to it.


**TODO:**

* What the different `fab_modes` do.
* @hosts, @mode and the other decorators
* simulating "roles" with @hosts


[PKey]: http://www.lag.net/paramiko/docs/paramiko.PKey-class.html
[connect]: http://www.lag.net/paramiko/docs/paramiko.SSHClient-class.html#connect

