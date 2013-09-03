import docutils
import ipdb


class issue(docutils.nodes.Element):
    pass

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
    lines = {'master': []}
    for obj in reversed(entries):
        # The 'actual' intermediate object we want to focus on is wrapped first
        # in a LI, then a P.
        focus = obj[0][0]
        # Releases 'eat' the entries in their line's list and get added to the
        # final data structure. They also inform new release-line 'buffers'.
        if isinstance(focus, release):
            line = get_line(focus)
            print "RELEASE (%s line): %s" % (line, focus.number)
            # New release line/branch detected. Create it & dump master into
            # this new release.
            if line not in lines:
                print "\tNew line, allocating buffer & flushing %s from master" % len(lines['master'])
                lines[line] = []
                releases[focus.number] = {
                    'obj': focus,
                    'entries': lines['master']
                }
                lines['master'] = []
            # Existing line -> empty out its bucket into new release
            else:
                print "\tFlushing %s from %s" % (len(lines[line]), line)
                releases[focus.number] = {
                    'obj': focus,
                    'entries': lines[line]
                }
                lines[line] = []
        # Entries get copied into all release lines' buckets.
        # Unsupported release lines will 'waste' space but there's no way to
        # determine actual support termination, so whatever.
        elif isinstance(focus, issue):
            print "ENTRY: %s" % focus
            for line in lines:
                lines[line].append(focus)
            print "\tAdded to %s release lines" % len(lines)

    ipdb.set_trace()


def setup(app):
    app.add_node(issue)
    #app.connect('doctree-resolved', generate_changelog)
    app.connect('doctree-read', generate_changelog)
