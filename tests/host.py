from spec import Spec, skip, eq_

from fabric import Host


class Host_(Spec):
    class init:
        "__init__"

        def no_args(self):
            h = Host()
            eq_(h.name, None)
            eq_(h.aliases, [])

        def hostname(self):
            h = Host('target')
            eq_(h.name, 'target')
            eq_(h.aliases, [])

        def hostname_and_aliases(self):
            h = Host('target', aliases=['othername'])
            eq_(h.name, 'target')
            eq_(h.aliases, ['othername'])
