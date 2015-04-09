from invoke.runners import Runner


class Remote(Runner):
    """
    Run a shell command over an SSH connection.

    This class subclasses `invoke.runners.Runner`; please see its documentation
    for most public API details.

    .. note::
        `.Remote`'s ``__init__`` method expects a `.Connection` (or subclass)
        instance for its ``context`` argument.
    """
    # TODO: Needs to fully implement run_direct() and run_pty(), no shared code
    # (the factored outer bits are in invoke.runner.run())
    
    def run_direct(self, command, warn, hide, encoding):
        channel = self.context._create_session()
        channel.exec_command(command)

        # obtain pipes for stdin/out/err (TODO: arbitrary args for these)
        # create objects to hold streams
        # define thread target appending to objects & printing to streams
        #   (TODO: host prefixes depending on configuration)
        # create thread objects, add to list, start them
        # wait on remote proc (may require loop+sleep)
        # join threads
        # tie up captured stderr/out into single string objs
        # return those + exit code (+ exception? does that make sense here as
        #    well as wherever it was originally intended in Local?)

        return ("", "", 0, None)


class RemoteSudo(Remote):
    """
    Run a command over SSH, wrapped in ``sudo``.
    """
    # Needs to do what Remote does, except:
    # * modify the command string (implies that's a subroutine or hooks based
    # thing)
    # * handle password prompting and playback (prob also a subroutine?)
    # TODO: this may want to just become generic except-like handling (like fab
    # 1 'prompts' stuff) in Remote, then this simply automates wrapping w/ sudo
    # -c (i.e. one could get 100% same effect by manually doing run("sudo -c
    # 'my command'")).
    # TODO: that probably just means a method on Connection and no new class
    # here.
    pass
