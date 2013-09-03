import docutils
import ipdb


class issue(docutils.nodes.Element):
    @property
    def type(self):
        return self.attributes['type_']

    @property
    def backported(self):
        return self.attributes['backported']

    @property
    def number(self):
        return self.attributes['number']

class release(docutils.nodes.Element):
    @property
    def number(self):
        return self.attributes['number']


def get_line(obj):
    # 1.2.7 -> 1.2
    return '.'.join(obj.number.split('.')[:-1])

def first_releases(entries):
    ret = []
    while not isinstance(entries[0], issue):
        ret.append(entries.pop(0))
    return ret, entries

def generate_changelog(app, doctree):
    # This seems to be the cleanest way to tell what a not-fully-parsed
    # document's 'name' is. Also lol @ not fully implementing dict protocol.
    source = doctree.children[0]
    if 'changelog' not in source.get('names', []):
        return
    # Second item inside main document is the 'modern' changelog bullet-list
    # object, whose children are the nodes we care about.
    entries = source.children[1].children
    # Walk from back to front, consuming entries & copying them into
    # per-release buckets as releases are encountered.
    releases = {}
    lines = {'unreleased': []}
    for obj in reversed(entries):
        # The 'actual' intermediate object we want to focus on is wrapped first
        # in a LI, then a P.
        focus = obj[0][0]
        # Releases 'eat' the entries in their line's list and get added to the
        # final data structure. They also inform new release-line 'buffers'.
        if isinstance(focus, release):
            line = get_line(focus)
            # New release line/branch detected. Create it & dump unreleased into
            # this new release.
            if line not in lines:
                lines[line] = []
                releases[focus.number] = {
                    'obj': focus,
                    'entries': lines['unreleased']
                }
                lines['unreleased'] = []
            # Existing line -> empty out its bucket into new release
            else:
                releases[focus.number] = {
                    'obj': focus,
                    'entries': lines[line]
                }
                lines[line] = []
        # Entries get copied into release line buckets as follows:
        # * Everything goes into 'unreleased' so it can be used in new lines.
        # * Bugfixes (but not support or feature entries) go into all release
        # lines, not just 'unreleased'.
        # * However, support/feature entries marked as 'backport' go into all
        # release lines as well, on the assumption that they were released to
        # all active branches.
        elif isinstance(focus, issue):
            lines['unreleased'].append(focus)
            if focus.type == 'bug' or focus.backported:
                for line in lines:
                    lines[line].append(focus)
        # Entries not yet released get special 'release' entries (that lack an
        # actual release object).
        for line, items in lines:
            releases['.'.join(line, 'X')] = {
                'entries': items
            }

    ipdb.set_trace()


def setup(app):
    app.add_node(issue)
    #app.connect('doctree-resolved', generate_changelog)
    app.connect('doctree-read', generate_changelog)
