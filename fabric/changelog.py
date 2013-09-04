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

def construct_releases(entries):
    # Walk from back to front, consuming entries & copying them into
    # per-release buckets as releases are encountered. Store releases in order.
    releases = []
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
                releases.append({
                    'obj': focus,
                    'entries': lines['unreleased']
                })
                lines['unreleased'] = []
            # Existing line -> empty out its bucket into new release
            else:
                releases.append({
                    'obj': focus,
                    'entries': lines[line]
                })
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
        for line, items in lines.iteritems():
            number = "%s.X" % line
            if line == 'unreleased':
                line = number = 'master'
            nodelist = [
                docutils.nodes.strong(text='Unreleased (%s)' % line),
                docutils.nodes.reference(
                    text="Fabric %s" % number,
                    refuri="https://github.com/fabric/fabric/tree/%s" % line,
                    classes=['changelog-release']
                )
            ]
            releases.append({
                'obj': release(number=number, date=None, nodelist=nodelist),
                'entries': items
            })
    return releases

def construct_nodes(releases):
    nodes = []
    # Reverse the list again so the final display is newest on top
    for d in reversed(releases):
        if not d['entries']:
            continue
        release = d['obj']
        entries = [
            docutils.nodes.list_item('',
                docutils.nodes.paragraph('', *x.attributes['nodelist'])
            )
            for x in d['entries']
        ]
        # Release header
        # TODO: create actual header node, durr
        nodes.extend(release.attributes['nodelist'])
        # Entry list
        list_ = docutils.nodes.bullet_list('', *entries)
        nodes.append(list_)
    return nodes

def generate_changelog(app, doctree):
    # This seems to be the cleanest way to tell what a not-fully-parsed
    # document's 'name' is. Also lol @ not fully implementing dict protocol.
    source = doctree.children[0]
    if 'changelog' not in source.get('names', []):
        return
    # Second item inside main document is the 'modern' changelog bullet-list
    # object, whose children are the nodes we care about.
    changelog = source.children.pop(1)
    # Walk + parse into release mapping
    releases = construct_releases(changelog.children)
    # Construct new set of nodes to replace the old, and we're done
    source.children[1:1] = construct_nodes(releases)
    ipdb.set_trace()


def setup(app):
    #app.connect('doctree-resolved', generate_changelog)
    app.connect('doctree-read', generate_changelog)
