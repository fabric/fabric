from spec import Spec, eq_

from fabric import ThreadingGroup as Group


class Group_(Spec):
    def simple_command(self):
        group = Group('localhost', '127.0.0.1')
        result = group.run('echo foo', hide=True)
        eq_(
            [x.stdout.strip() for x in result.values()],
            ['foo', 'foo'],
        )
