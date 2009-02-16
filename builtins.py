"""
Builtin Fabric commands such as help and list.
"""


#@mode("broad")
def help(*args, **kwargs):
    """
    Display Fabric usage help, or help for a given command.
    
    You can provide help with a parameter and get more detailed help for a
    specific command. For instance, to learn more about the list command, you
    could run `fab help:list`.
    
    If you are developing your own fabfile, then you might also be interested
    in learning more about operations. You can do this by running help with the
    `op` parameter set to the name of the operation you would like to learn
    more about. For instance, to learn more about the `run` operation, you
    could run `fab help:op=run`.

    Fabric also exposes some utility decorators for use with your own commands.
    Run help with the `dec` parameter set to the name of a decorator to learn
    more about it.
    
    """
    if args:
        for k in args:
            if k in COMMANDS:
                _print_help_for_in(k, COMMANDS)
            elif k in OPERATIONS:
                _print_help_for_in(k, OPERATIONS)
            elif k in ['op', 'operation']:
                _print_help_for_in(kwargs[k], OPERATIONS)
            elif k in ['dec', 'decorator']:
                _print_help_for_in(kwargs[k], DECORATORS)
            else:
                _print_help_for(k, None)
    else:
        print("""
    Fabric is a simple pythonic remote deployment tool.
    
    Type `fab list` to get a list of available commands.
    Type `fab help:help` to get more information on how to use the built in
    help.
    
    """)


def about(*args, **kwargs):
    "Display Fabric version, warranty and license information"
    print(__about__ % ENV)


#@mode("broad")
# TODO: add actual flag args/opts to Fabric, and make this e.g. -l / --list
def list_commands(*args, **kwargs):
    """
    Display a list of commands with descriptions.
    
    By default, the list command prints a list of available commands, with a
    short description (if one is available). However, the list command can also
    print a list of available operations if you provide it with the `ops` or
    `operations` parameters, or it can print a list of available decorators if
    provided with the `dec` or `decorators` parameters.
    """
    if args:
        for k in args:
            if k in ['cmds', 'commands']:
                print("Available commands are:")
                _list_objs(COMMANDS)
            elif k in ['ops', 'operations']:
                print("Available operations are:")
                _list_objs(OPERATIONS)
            elif k in ['dec', 'decorators']:
                print("Available decorators are:")
                _list_objs(DECORATORS)
            else:
                print("Don't know how to list '%s'." % k)
                print("Try one of these instead:")
                print(_indent('\n'.join([
                    'cmds', 'commands',
                    'ops', 'operations',
                    'dec', 'decorators',
                ])))
                sys.exit(1)
    else:
        print("Available commands are:")
        _list_objs(COMMANDS)


#@mode("broad")
def let(*args, **kwargs):
    """
    Set a Fabric variable.
    
    Example:
    
        $fab let:fab_user=billy,other_var=other_value
    """
    for k, v in kwargs.items():
        if isinstance(v, basestring):
            v = (v % ENV)
        ENV[k] = v


#@mode("broad")
def shell(*args, **kwargs):
    """
    Start an interactive shell connection to the specified hosts.
    
    Optionally takes a list of hostnames as arguments, if Fabric is, by
    the time this command runs, not already connected to one or more
    hosts. If you provide hostnames and Fabric is already connected, then
    Fabric will, depending on `fab_fail`, complain and abort.
    
    The `fab_fail` variable can be overwritten with the `set` command, or
    by specifying an additional `fail` argument.
    
    Examples:
    
        $fab shell
        $fab shell:localhost,127.0.0.1
        $fab shell:localhost,127.0.0.1,fail=warn
    
    """
    # expect every arg w/o a value to be a hostname
    hosts = filter(lambda k: not kwargs[k], kwargs.keys())
    if hosts:
        if CONNECTIONS:
            _fail(kwargs, "Already connected to predefined fab_hosts.")
        ENV['fab_hosts'] = hosts
    def lines():
        try:
            while True:
                yield raw_input("fab> ")
        except EOFError:
            # user pressed ctrl-d
            print
    for line in lines():
        if line == 'exit':
            break
        elif line.startswith('sudo '):
            sudo(line[5:], fail='warn')
        else:
            run(line, fail='warn')
