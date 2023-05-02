"""
CLI entrypoint & parser configuration.

Builds on top of Invoke's core functionality for same.
"""

import getpass

from invoke import Argument, Collection, Exit, Program
from invoke import __version__ as invoke
from paramiko import __version__ as paramiko, Agent

from . import __version__ as fabric
from . import Config, Executor


class Fab(Program):
    def print_version(self):
        super().print_version()
        print("Paramiko {}".format(paramiko))
        print("Invoke {}".format(invoke))

    def core_args(self):
        core_args = super().core_args()
        my_args = [
            Argument(
                names=("H", "hosts"),
                help="Comma-separated host name(s) to execute tasks against.",
            ),
            Argument(
                names=("i", "identity"),
                kind=list,  # Same as OpenSSH, can give >1 key
                # TODO: automatically add hint about iterable-ness to Invoke
                # help display machinery?
                help="Path to runtime SSH identity (key) file. May be given multiple times.",  # noqa
            ),
            Argument(
                names=("list-agent-keys",),
                kind=bool,
                help="Display ssh-agent key list, and exit.",
            ),
            # TODO: worth having short flags for these prompt args?
            Argument(
                names=("prompt-for-login-password",),
                kind=bool,
                help="Request an upfront SSH-auth password prompt.",
            ),
            Argument(
                names=("prompt-for-passphrase",),
                kind=bool,
                help="Request an upfront SSH key passphrase prompt.",
            ),
            Argument(
                names=("S", "ssh-config"),
                help="Path to runtime SSH config file.",
            ),
            Argument(
                names=("t", "connect-timeout"),
                kind=int,
                help="Specifies default connection timeout, in seconds.",
            ),
        ]
        return core_args + my_args

    @property
    def _remainder_only(self):
        # No 'unparsed' (i.e. tokens intended for task contexts), and remainder
        # (text after a double-dash) implies a contextless/taskless remainder
        # execution of the style 'fab -H host -- command'.
        # NOTE: must ALSO check to ensure the double dash isn't being used for
        # tab completion machinery...
        return (
            not self.core.unparsed
            and self.core.remainder
            and not self.args.complete.value
        )

    def load_collection(self):
        # Stick in a dummy Collection if it looks like we were invoked w/o any
        # tasks, and with a remainder.
        # This isn't super ideal, but Invoke proper has no obvious "just run my
        # remainder" use case, so having it be capable of running w/o any task
        # module, makes no sense. But we want that capability for testing &
        # things like 'fab -H x,y,z -- mycommand'.
        if self._remainder_only:
            # TODO: hm we're probably not honoring project-specific configs in
            # this branch; is it worth having it assume CWD==project, since
            # that's often what users expect? Even tho no task collection to
            # honor the real "lives by task coll"?
            self.collection = Collection()
        else:
            super().load_collection()

    def no_tasks_given(self):
        # As above, neuter the usual "hey you didn't give me any tasks, let me
        # print help for you" behavior, if necessary.
        if not self._remainder_only:
            super().no_tasks_given()

    def create_config(self):
        # Create config, as parent does, but with lazy=True to avoid our own
        # SSH config autoload. (Otherwise, we can't correctly load _just_ the
        # runtime file if one's being given later.)
        self.config = self.config_class(lazy=True)
        # However, we don't really want the parent class' lazy behavior (which
        # skips loading system/global invoke-type conf files) so we manually do
        # that here to match upstream behavior.
        self.config.load_base_conf_files()
        # And merge again so that data is available.
        # TODO: really need to either A) stop giving fucks about calling
        # merge() "too many times", or B) make merge() itself determine whether
        # it needs to run and/or just merge stuff that's changed, so log spam
        # isn't as bad.
        self.config.merge()

    def update_config(self):
        # Note runtime SSH path, if given, and load SSH configurations.
        # NOTE: must do parent before our work, in case users want to disable
        # SSH config loading within a runtime-level conf file/flag.
        super().update_config(merge=False)
        self.config.set_runtime_ssh_path(self.args["ssh-config"].value)
        self.config.load_ssh_config()
        # Load -i identity file, if given, into connect_kwargs, at overrides
        # level.
        # TODO: this feels a little gross, but since the parent has already
        # called load_overrides, this is best we can do for now w/o losing
        # data. Still feels correct; just might be cleaner to have even more
        # Config API members around this sort of thing. Shrug.
        connect_kwargs = {}
        path = self.args["identity"].value
        if path:
            connect_kwargs["key_filename"] = path
        # Ditto for connect timeout
        timeout = self.args["connect-timeout"].value
        if timeout:
            connect_kwargs["timeout"] = timeout
        # Secrets prompts that want to happen at handoff time instead of
        # later/at user-time.
        # TODO: should this become part of Invoke proper in case other
        # downstreams have need of it? E.g. a prompt Argument 'type'? We're
        # already doing a similar thing there for sudo password...
        if self.args["prompt-for-login-password"].value:
            prompt = "Enter login password for use with SSH auth: "
            connect_kwargs["password"] = getpass.getpass(prompt)
        if self.args["prompt-for-passphrase"].value:
            prompt = "Enter passphrase for use unlocking SSH keys: "
            connect_kwargs["passphrase"] = getpass.getpass(prompt)
        self.config._overrides["connect_kwargs"] = connect_kwargs
        # Since we gave merge=False above, we must do it ourselves here. (Also
        # allows us to 'compile' our overrides manipulation.)
        self.config.merge()

    # TODO: make this an explicit hookpoint in Invoke, i.e. some default-noop
    # method called at the end of parse_core() that we can override here
    # instead of doing this.
    def parse_core(self, *args, **kwargs):
        super().parse_core(*args, **kwargs)
        if self.args["list-agent-keys"].value:
            for key in Agent().get_keys():
                real = key.inner_key
                tpl = "{} {} {} ({})"
                print(tpl.format(
                    key.get_bits(),
                    key.fingerprint,
                    key.comment,
                    key.algorithm_name,
                ))
            raise Exit


# Mostly a concession to testing.
def make_program():
    return Fab(
        name="Fabric",
        version=fabric,
        executor_class=Executor,
        config_class=Config,
    )


program = make_program()
