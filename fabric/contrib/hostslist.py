import string


class _HostTreeNode(object):
    ROOTNODE = "/"
    PATHSEP = "/"
    HOSTSEP = ":"

    def __init__(self, namespace=[ROOTNODE], host=None, parent=None):
        self.children = []
        self.hosts = []
        self.name = namespace[0].lower()
        self.parent = parent
        self.add(namespace[1:], host)

    def add(self, namespace, host):
        '''
        Add a Host to the Tree
        :param namespace: List of Strings with the namespace of the Host
        :param host: Strinf with the Host name
        '''
        if namespace:
            child = self._getchild(namespace)
            if child == None:
                self.children.append(_HostTreeNode(namespace, host, self))
            else:
                child.add(namespace[1:], host)
        elif host != None:
            self.hosts.append(host.lower())

    def _getchild(self, namespace):
        '''
        :returns: the Children of a Node
        :param namespace: List of Strings with the namespace for the Node
        '''
        if namespace:
            for child in self.children:
                if child.name == namespace[0]:
                    return child

    def get_namespace(self, namespace=None):
        '''
        :returns: The Namespace of a Node Object
        :param namespace: Namespace for recursion
        '''
        if namespace is None:
            namespace = []
        if self.parent is not None:
            namespace.insert(0, self.name)
            self.parent.get_namespace(namespace)
        return namespace

    def get_namespace_string(self):
        '''
        :returns: The string representzation of a namespace
        '''
        namespace = self.get_namespace()
        pathstring = _HostTreeNode.PATHSEP
        while namespace:
            pathstring += namespace[0]
            del namespace[0]
            if namespace:
                pathstring += _HostTreeNode.PATHSEP
        return pathstring

    def find_node(self, namespace=None):
        '''
        :returns: A Node Object. None if not found.
        :param namespace: Namespace of node to be found.
        '''
        if namespace:
            if self.name == _HostTreeNode.ROOTNODE:
                child = self._getchild(namespace)
                if child is not None:
                    return child.find_node(namespace)

            if self.name == namespace[0]:
                nsp = namespace[1:]
                if not nsp:
                    return self
                else:
                    child = self._getchild(nsp)
                    if child is not None:
                        return child.find_node(nsp)
        else:
            return self

    def has_hosts(self, namespace):
        '''
        :returns: True if Node has any hosts.
        :param namespace: Namespace of Node
        '''
        node = self.find_node(namespace)
        if node is not None:
            if node.hosts:
                return True
            else:
                return False

    def has_host(self, host, namespace=None,):
        '''
        :returns: True if Node has a specific Host.
        :param host: The Host to look for
        :param namespace: Namespace of Node
        '''
        node = self.find_node(namespace)
        if node is not None:
            return host in node.hosts
        else:
            return False

    def get_hosts(self, namespace=None):
        '''
        :returns: All Hosts of a Node.
        :param namespace: Namespace of Node
        '''
        node = self.find_node(namespace)
        if node is not None:
            return node.hosts

    def get_nodes(self, namespace=None, recursive=False):
        '''
        :returns: List of Child Nodes.
        :param namespace: Namespace of Node
        :param recursive: If True list shall contain Children of Children
        '''
        return_nodes = []
        node = self.find_node(namespace)
        if node is not None:
            return_nodes.append(node)
            if recursive:
                for cld in node.children:
                    return_nodes.extend(cld.get_nodes(None, True))
        return return_nodes

    def __str__(self, indent=""):
        return_string = indent + self.name + "\n"
        for host in self.hosts:
            return_string += indent + " -" + host + "\n"
        for child in self.children:
            return_string += child.__str__(indent + "  ")
        return return_string


class HostException(Exception):
    '''
    Exception That Identifies trouble with the Host Selection
    '''


class HostSelection(object):
    '''
    Manages wich hosts of a list of Hosts shall be selected for further use.
    Hosts may have a Namespace that groups them.
    The namespace is independent of a fqdn.
    Namespace and host parameter accept * as a Placeholder for all
    The Hostselcten accepts ! as a placeholder for Exlude in select lists
    '''

    def __init__(self, hosts=None):
        self.hasfile = False
        if hosts is not None:
            if isinstance(hosts, _HostTreeNode):
                self.root = hosts
            else:
                self.root = _parse(hosts)
            self.hasfile = True
        else:
            self.root = _HostTreeNode()
        self.selections = []
        self.exclusions = []

    def __str__(self, *args, **kwargs):
        return self.root.__str__()

    def select(self, namespace, host):
        '''
        Selects a Host
        :param namespace: List of strings with the Namespace of te Host.
        :param host: The Host
        '''
        self.selections.append([namespace, host])

    def exclude(self, namespace, host):
        '''
        Excludes a Host
        :param namespace: List of strings with the Namespace of the Host.
        :param host: The Host
        '''
        self.exclusions.append([namespace, host])

    def parse_cmd(self, cmd):
        '''
        Parse A command string.
        Commands are seperated by ;.
        ! Is a Placeholder for Exclude
        :param cmd: The Command String
        '''
        args = cmd.split(';')
        for arg in args:
            if arg.startswith("!"):
                sel = HostSelection.parseSelection(arg[1:])
                self.exclude(sel[0], sel[1])
            else:
                sel = HostSelection.parseSelection(arg)
                self.select(sel[0], sel[1])
                if not self.hasfile:
                    self.root.add(sel[0], sel[1])

    @staticmethod
    def parseSelection(selection):
        '''
        Parse A selection String into a Namespace and Host
        :param selection: The Selection String
        :returns: A list with The Namespace in first \
        element and the Host in second
        '''
        spl = selection.strip()
        spl = spl.lower()
        spl = spl.partition(_HostTreeNode.HOSTSEP)
        if spl[0].startswith(_HostTreeNode.PATHSEP):
            namespace = _parsenamespace(spl[0])
        elif spl[0] == "*":
            namespace = [spl[0]]
        else:
            namespace = []

        if spl[2]:
            return [namespace, spl[2]]
        elif namespace == []:
            return [namespace, spl[0]]
        else:
            return [namespace, "*"]

    def _get_selected(self, pattern):
        for pat in pattern:
            if len(pat[0]) == 0:
                namespace = [_HostTreeNode.ROOTNODE]
            else:
                namespace = pat[0]
            if namespace[-1] == "*":
                nodes = self.root.get_nodes(namespace[0:-1], True)
            else:
                nodes = [self.root.find_node(namespace)]

            for node in nodes:
                if pat[1] == "*":
                    hosts = node.get_hosts()
                else:
                    hosts = [pat[1]]
                for host in hosts:
                    if node.has_host(host):
                        nsp = node.get_namespace_string()
                        yield [nsp + _HostTreeNode.HOSTSEP + host, host]

    def flatten(self):
        '''
        Flatten the Selection tree into a list of Host names,
        :returns: A List of Host Names (No Namespaces)
        '''
        exclude_hosts = []
        for host in self._get_selected(self.exclusions):
            exclude_hosts.append(host[0])

        selected_hosts = set()
        for host in self._get_selected(self.selections):
            if host[0] not in exclude_hosts:
                selected_hosts.add(host[1])

        return list(selected_hosts)


def _parsenamespace(nsp_string):
    namespace = nsp_string[1:].split(_HostTreeNode.PATHSEP)
    for nsp in namespace:
        if nsp == "":
            raise HostException("The Namespace " + nsp_string + \
                                "contains an illegal empty node")
        for char in nsp:
            if char not in string.ascii_lowercase \
                and char not in string.digits \
                and char != "*":
                raise HostException("The Namespace " + nsp_string + \
                                    " contains an illegal character")
    return namespace


def _parse(lines):
    root = _HostTreeNode()
    namespace = []
    for line in lines:
        line = line.partition("#")[0]
        line = line.strip()
        line = line.lower()
        if line is "":
            continue
        if line.startswith("["):
            nsp = line[1:line.index("]")]
            if not nsp.startswith("/"):
                nsp = "/" + nsp
            namespace = _parsenamespace(nsp)
            continue
        root.add(namespace, line)
    return root


def select_hosts_from_file(hostsfile, cmd=""):
    '''
    Helper Function to create the HostSelection from a file and send all
    Commands to that selection.
    :param hostsfile: An iterable Object with Lines of Strings. eg. \
    An File Object
    :param cmd: A Command string
    '''
    selection = HostSelection(hostsfile)
    selection.parse_cmd(cmd)
    return selection
