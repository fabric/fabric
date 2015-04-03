from invoke.runners import Runner


class Remote(Runner):
    """
    Run a command over SSH.
    """
    # Needs to fully implement run() and run_pty(), no shared code (the
    # factored outer bits are in invoke.runner.run())
    pass


class RemoteSudo(Remote):
    """
    Run a command over SSH, wrapped in ``sudo``.
    """
    # Needs to do what Remote does, except:
    # * modify the command string (implies that's a subroutine or hooks based
    # thing)
    # * handle password prompting and playback (prob also a subroutine?)
    pass
