import docutils
import ipdb


class issue(docutils.nodes.Element):
    @property
    def type(self):
        return self['type_']

    @property
    def backported(self):
        return self['backported']

    @property
    def major(self):
        return self['major']

    @property
    def number(self):
        return self.get('number', None)

class release(docutils.nodes.Element):
    @property
    def number(self):
        return self['number']


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
        focus, rest = obj[0][0], obj[0][1:]
        # Releases 'eat' the entries in their line's list and get added to the
        # final data structure. They also inform new release-line 'buffers'.
        # Release lines should have an empty 'rest' so it's ignored.
        if isinstance(focus, release):
            line = get_line(focus)
            # New release line/branch detected. Create it & dump unreleased into
            # this new release. Skip non-major bugs.
            if line not in lines:
                lines[line] = []
                releases.append({
                    'obj': focus,
                    'entries': [
                        x
                        for x in lines['unreleased'] 
                        if x.type in ('feature', 'support') or x.major
                    ]
                })
                lines['unreleased'] = []
            # Existing line -> empty out its bucket into new release.
            # Skip 'major' bugs as those "belong" to the next release.
            else:
                releases.append({
                    'obj': focus,
                    'entries': [x for x in lines[line] if not x.major],
                })
                lines[line] = []
        # Entries get copied into release line buckets as follows:
        # * Everything goes into 'unreleased' so it can be used in new lines.
        # * Bugfixes (but not support or feature entries) go into all release
        # lines, not just 'unreleased'.
        # * However, support/feature entries marked as 'backport' go into all
        # release lines as well, on the assumption that they were released to
        # all active branches.
        # * The 'rest' variable (which here is the bug description, vitally
        # important!) is preserved by stuffing it into the focus (issue)
        # object.
        else:
            # Handle rare-but-valid non-issue-attached line items, which are
            # always bugs. (They are their own description.)
            if not isinstance(focus, issue):
                focus = issue(type_='bug', nodelist=[focus], backported=False, major=False, description=[focus])
            else:
                focus.attributes['description'] = rest
            # Bugs go errywhere
            if focus.type == 'bug' or focus.backported:
                for line in lines:
                    lines[line].append(focus)
            # Non-bugs only go into unreleased (next release)
            else:
                lines['unreleased'].append(focus)

    # Entries not yet released get special 'release' entries (that lack an
    # actual release object).
    # FIXME: this isn't actually feasible because, due to no ability to mark
    # lines extinct, ALL lines get their own 'unreleased' release.
    #for line, items in lines.iteritems():
    #    number = "%s.X" % line
    #    if line == 'unreleased':
    #        line = number = 'master'
    #    nodelist = [
    #        docutils.nodes.strong(text='Unreleased (%s)' % line),
    #        docutils.nodes.reference(
    #            text="Fabric %s" % number,
    #            refuri="https://github.com/fabric/fabric/tree/%s" % line,
    #            classes=['changelog-release']
    #        )
    #    ]
    #    releases.append({
    #        'obj': release(number=number, date=None, nodelist=nodelist),
    #        'entries': items
    #    })
    return releases

def construct_nodes(releases):
    nodes = []
    # Reverse the list again so the final display is newest on top
    for d in reversed(releases):
        if not d['entries']:
            continue
        release = d['obj']
        # Use docutils.nodes.Node.deepcopy to deepcopy the description nodes.
        # If this is not done, multiple references to the same object (e.g. a
        # reference object in the description of #649, which is then copied
        # into 2 different release lists) will end up in the doctree, which
        # makes subsequent parse steps very angry (index() errors).
        entries = [
            docutils.nodes.list_item('',
                docutils.nodes.paragraph('', *(x['nodelist'] + map(lambda x: x.deepcopy(), x['description'])))
            )
            for x in d['entries']
        ]
        # Release header
        # TODO: create actual header node, durr
        nodes.extend(docutils.nodes.paragraph('', release['nodelist']))
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


def setup(app):
    #app.connect('doctree-resolved', generate_changelog)
    app.connect('doctree-read', generate_changelog)
