from invoke import FilesystemLoader


class FabfileLoader(FilesystemLoader):
    # TODO: we may run into issues re: swapping loader "strategies" (eg
    # FilesystemLoader vs...something else eventually) versus this sort of
    # "just tweaking DEFAULT_COLLECTION_NAME" setting. Maybe just make the
    # default collection name itself a runtime option?
    DEFAULT_COLLECTION_NAME = 'fabfile'
