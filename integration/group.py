from spec import Spec, eq_

from fabric import ThreadingGroup as Group


class Group_(Spec):
    def simple_command_on_multiple_hosts(self):
        """
        Run command on localhost...twice!
        """
        group = Group('localhost', 'localhost')
        result = group.run('echo foo', hide=True)
        # NOTE: currently, the result will only be 1 object, because both of
        # them will end up as the same key. Derp.
        eq_(result[group[0]].stdout, "foo\n")
