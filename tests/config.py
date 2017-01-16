from fabric.config import Config

from mock import patch
from spec import Spec, eq_


class Config_(Spec):
    def defaults_to_merger_of_global_defaults(self):
        # I.e. our global_defaults + Invoke's global_defaults
        c = Config()
        # From invoke's global_defaults
        eq_(c.run.warn, False)
        # From ours
        eq_(c.port, 22)

    def has_various_Fabric_specific_default_keys(self):
        # NOTE: Duplicates some other tests but we're now starting to
        # grow options not directly related to user/port stuff, so best
        # to have at least one test listing all expected keys.
        for keyparts in (
            ('port',),
            ('user',),
            ('forward_agent',),
            ('sudo', 'prompt'),
            ('sudo', 'password'),
        ):
            obj = Config()
            for key in keyparts:
                err = "Didn't find expected config key path '{0}'!"
                assert key in obj, err.format(".".join(keyparts))
                obj = obj[key]

    def our_defaults_override_invokes(self):
        "our defaults override invoke's"
        with patch.object(
            Config,
            'global_defaults',
            return_value={
                'run': {'warn': "nope lol"},
                'user': 'me',
                'port': 22,
                'forward_agent': False,
            }
        ):
            # If our global_defaults didn't win, this would still
            # resolve to False.
            eq_(Config().run.warn, "nope lol")

    def we_override_replace_env(self):
        # This value defaults to False in Invoke proper.
        eq_(Config().run.replace_env, True)
