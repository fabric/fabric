from spec import Spec, skip

from fabric import transfer


# TODO: pull in all edge/corner case tests from fabric v1

class Transfer_(Spec):
    class init:
        "__init__"
        def requires_connection(self):
            # Transfer() -> explodes
            # Transfer(Connection()) -> happy, exposes an attribute
            skip()

    class get:
        def preserves_remote_mode_by_default(self):
            # remote foo.txt is something unlikely to be default local
            # umask (but still readable by ourselves) -> get() -> local
            # file matches remote mode.
            skip()

        class no_local_path:
            def remote_relative_path_to_local_cwd(self):
                # cxn.get('foo.txt') -> ./foo.txt
                skip()

            def remote_absolute_path_to_local_cwd(self):
                # cxn.get('/tmp/foo.txt') -> ./foo.txt
                skip()

        class has_local_path:
            def remote_relative_path_to_local_relative_path(self):
                # cxn.get('foo.txt', local='bar.txt') -> ./bar.txt
                skip()

            def remote_absolute_path_to_local_relative_path(self):
                # cxn.get('/tmp/foo.txt', local='bar.txt') -> ./bar.txt
                skip()

            def remote_relative_path_to_local_absolute_path(self):
                # cxn.get('foo.txt', local='/tmp/bar.txt') -> /tmp/bar.txt
                skip()

            def remote_absolute_path_to_local_absolute_path(self):
                # cxn.get('/tmp/foo.txt', local='/tmp/bar.txt') -> /tmp/bar.txt
                skip()
