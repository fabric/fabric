# "Integration test" for Fabric to be run occasionally / before releasing.
# Executes idempotent/nonthreatening commands against localhost by default.

from __future__ import with_statement

from fabric.api import *


@hosts('localhost')
def test():
    flags = (True, False)
    funcs = (run, sudo)
    cmd = "ls /"
    line = "#" * 72
    for shell in flags:
        for pty in flags:
            for combine_stderr in flags:
                for func in funcs:
                    print(">>> %s(%s, shell=%s, pty=%s, combine_stderr=%s)" % (
                        func.func_name, cmd, shell, pty, combine_stderr))
                    print(line)
                    func(
                        cmd,
                        shell=shell,
                        pty=pty,
                        combine_stderr=combine_stderr
                    )
                    print(line + "\n")
