import docutils
import ipdb


class issue(docutils.nodes.Element):
    pass

class release(docutils.nodes.Element):
    pass


def generate_changelog(app, doctree):
    # This seems to be the cleanest way to tell what a not-fully-parsed
    # document's 'name' is. Also lol @ not fully implementing dict protocol.
    source = doctree.children[0]
    if 'changelog' not in source.get('names', []):
        return
    # Second item inside main document is the 'modern' changelog bullet-list
    # object, whose children are the nodes we care about.
    entries = source.children[1].children
    ipdb.set_trace()


def setup(app):
    app.add_node(issue)
    #app.connect('doctree-resolved', generate_changelog)
    app.connect('doctree-read', generate_changelog)
