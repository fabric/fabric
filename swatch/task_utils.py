from fabric.utils import abort, indent
from fabric import state


# For attribute tomfoolery
class _Dict(dict):
    pass


def _crawl(name, mapping):
    """
    ``name`` of ``'a.b.c'`` => ``mapping['a']['b']['c']``
    """
    key, _, rest = name.partition('.')
    value = mapping[key]
    if not rest:
        return value
    return _crawl(rest, value)


def crawl(name, mapping):
    try:
        result = _crawl(name, mapping)
        # Handle default tasks
        if isinstance(result, _Dict):
            if getattr(result, 'default', False):
                result = result.default
            # Ensure task modules w/ no default are treated as bad targets
            else:
                result = None
        return result
    except (KeyError, TypeError):
        return None


def merge(hosts, roles, exclude, roledefs):
    """
    Merge given host and role lists into one list of deduped hosts.
    """
    # Abort if any roles don't exist
    bad_roles = [x for x in roles if x not in roledefs]
    if bad_roles:
        abort("The following specified roles do not exist:\n%s" % (
            indent(bad_roles)
        ))

    # Coerce strings to one-item lists
    if isinstance(hosts, basestring):
        hosts = [hosts]

    # Look up roles, turn into flat list of hosts
    role_hosts = []
    for role in roles:
        value = roledefs[role]
        # Handle dict style roledefs
        if isinstance(value, dict):
            value = value['hosts']
        # Handle "lazy" roles (callables)
        if callable(value):
            value = value()
        role_hosts += value

    # Strip whitespace from host strings.
    cleaned_hosts = [x.strip() for x in list(hosts) + list(role_hosts)]
    # Return deduped combo of hosts and role_hosts, preserving order within
    # them (vs using set(), which may lose ordering) and skipping hosts to be
    # excluded.
    # But only if the user hasn't indicated they want this behavior disabled.
    all_hosts = cleaned_hosts
    if state.env.dedupe_hosts:
        deduped_hosts = []
        for host in cleaned_hosts:
            if host not in deduped_hosts and host not in exclude:
                deduped_hosts.append(host)
        all_hosts = deduped_hosts
    return all_hosts


def parse_kwargs(kwargs):
    new_kwargs = {}
    hosts = []
    roles = []
    exclude_hosts = []
    for key, value in kwargs.iteritems():
        if key == 'host':
            hosts = [value]
        elif key == 'hosts':
            hosts = value
        elif key == 'role':
            roles = [value]
        elif key == 'roles':
            roles = value
        elif key == 'exclude_hosts':
            exclude_hosts = value
        else:
            new_kwargs[key] = value
    return new_kwargs, hosts, roles, exclude_hosts
