from fabric.contrib import hostslist
import unittest
import os
from fabric.contrib.hostslist import HostSelection


class TestHostFile(unittest.TestCase):
    def setUp(self):
        self.mockhosts = [["org1", "sub1", "site1"], "host1"], \
                         [["org1", "sub1", "site1"], "host2"], \
                         [["org1", "sub1", "site1"], "host3"], \
                         [["org1", "sub1", "site1"], "host4"], \
                         [["org1", "sub1", "site1"], "host5"], \
                         [["org1", "sub1", "site1"], "host6"], \
                         [["org1", "sub1", "site1"], "host7"], \
                         [["org1", "sub1", "site1"], "host8"], \
                         [["org1", "sub1", "site2"], "host9"], \
                         [["org1", "sub1", "site2"], "host10"], \
                         [["org1", "sub1", "site2"], "host11"], \
                         [["org1", "sub1", "site2"], "host12"], \
                         [["org1", "sub1", "site4"], "host13"], \
                         [["org1", "sub1", "site4"], "host14"], \
                         [["org1", "sub1", "site3"], "host15"], \
                         [["org2", "sub1", "site1"], "host16"], \
                         [["org2", "sub1", "site1"], "host17"], \
                         [["org2", "sub1", "site1"], "host18"], \
                         [["org2", "sub2", "site4"], "host19"], \
                         [["org2", "sub2", "site4"], "host20"], \
                         [["org1", "sub1", "site3"], "host21"], \
                         [[], "host22"]

        self.mockfile = ("# comments\n",
                         "            ",
                         "host22\n",
                         "      #comment\n",
                         "[org1/sub1/site1]\n",
                         "host1\n",
                         "host2 #comment\n",
                         "host3#comment\n",
                         "host4\n",
                         "   host5\n",
                         "host6\n",
                         "host7\n",
                         "host8\n",
                         "#[/blah/foo]",
                         "[org1/sub1/site2]#comment\n",
                         "host9\n",
                         "host10\n",
                         "host11\n",
                         "host12\n",
                         "    [org1/sub1/site4]\n",
                         "host13\n",
                         "host14\n",
                         "    [/org1/sub1/site3]\n",
                         "host15\n",
                         "host21\n",
                         "[/org2/sub1/site1]\n",
                         "host16\n",
                         "host17\n",
                         "host18\n",
                         "[/org2/sub2/site4]\n",
                         "host19\n",
                         "host20\n",
                         )
        self.mockroot = hostslist._HostTreeNode()
        for host in self.mockhosts:
            self.mockroot.add(host[0], host[1])

    def test_datamodel(self):
        """
        The Data Model
        """
        for host in self.mockhosts:
            print self.mockroot
            assert self.mockroot.has_host(host[1], host[0]), \
            "A Host is missing in the Data"

            namespace = self.mockroot.find_node(host[0]).get_namespace()
            for idx, val in enumerate(host[0]):
                assert val == namespace[idx], "The Namespace is corrupt"

    def test_parse_file(self):
        """
        Parsed data
        """
        root = hostslist._parse(self.mockfile)
        for host in self.mockhosts:
            print host
            assert root.has_host(host[1], host[0]), \
            "A Host is missing in the Data"
        print root
        assert root.__str__() == self.mockroot.__str__()

    def test_explicit_single_select(self):
        """
        A lsingle host is explicitly selected
        """
        sel = hostslist.HostSelection(self.mockroot)
        namespace = self.mockhosts[12][0]
        host = self.mockhosts[12][1]
        sel.select(namespace, host)
        result = sel.flatten()
        print len(result)
        assert len(result) == 1, \
        "The returned host differs in size from the expected"
        print result[0], host
        assert result[0] == host, "The Host is wrong"

    def test_explicit_multiple_select(self):
        """
        A list of hosts is explicitly selected
        """
        sel = hostslist.HostSelection(self.mockroot)
        for host in self.mockhosts:
            sel.select(host[0], host[1])
        result = sel.flatten()
        print len(result), len(self.mockhosts)
        assert len(result) == len(self.mockhosts), \
        "The returned host differs in size from the expected"
        for host in self.mockhosts:
            print host[1], result
            assert host[1] in result, "A host is mising from the result"

    def test_explicit_single_exclude(self):
        """
        A list of hosts is explicitly excluded
        """
        sel = hostslist.HostSelection(self.mockroot)
        for host in self.mockhosts:
            sel.select(host[0], host[1])
        namespace = self.mockhosts[3][0]
        host = self.mockhosts[3][1]
        sel.exclude(namespace, host)
        result = sel.flatten()
        print len(self.mockhosts)
        print len(result), (len(self.mockhosts) - 1)
        assert len(result) == (len(self.mockhosts) - 1), \
        "The returned host differs in size from the expected"
        print host, result
        assert host not in result, "The excluded host was found in the result"

    def test_duplicate_host_removal(self):
        """
        Some Hosts are selected through multiple patterns thus can be double
        """
        self.mockroot.add(self.mockhosts[13][0], self.mockhosts[17][1])
        # one entry is multiplied the result size must stay the same
        sel = hostslist.HostSelection(self.mockroot)
        for host in self.mockhosts:
            sel.select(host[0], host[1])
        result = sel.flatten()
        print len(result), len(self.mockhosts)
        assert len(result) == len(self.mockhosts), \
        "The returned host differs in size from the expected"

    def test_explicit_multiple_exclude(self):
        """
        A list of hosts is explicitly excluded
        """
        sel = hostslist.HostSelection(self.mockroot)
        for host in self.mockhosts:
            sel.select(host[0], host[1])
        for host in self.mockhosts:
            sel.exclude(host[0], host[1])

        result = sel.flatten()
        assert len(result) == 0, \
        "The returned host differs in size from the expected"

    def test_wildcard_select_hosts(self):
        """
        A list of hosts is selected through wildcards
        """
        sel = hostslist.HostSelection(self.mockroot)
        namespace = self.mockhosts[3][0]
        host = "*"
        sel.select(namespace, host)
        count = 0
        for host in self.mockhosts:
            if cmp(host[0], namespace) == 0:
                count += 1
        result = sel.flatten()
        print len(result), count
        assert len(result) == count, \
        "The returned host differs in size from the expected"

    def test_wildcard_select_namespace(self):
        """
        A list of namespaces is selected through wildcards
        """
        sel = hostslist.HostSelection(self.mockroot)
        namespace = self.mockhosts[3][0][:]
        namespace[-1] = "*"
        print namespace
        host = "*"
        sel.select(namespace, host)

        count = 0
        for host in self.mockhosts:
            if len(host[0]) == 0:
                pass
            elif host[0][0] == namespace[0] and host[0][1] == namespace[1]:
                print host[0], host[1]
                count += 1
        print count
        result = sel.flatten()
        print result
        print len(result), count
        assert len(result) == count, \
        "The returned host differs in size from the expected"

    def test_wildcard_select_all(self):
        """
        A list of namespaces is selected through wildcards
        """
        sel = hostslist.HostSelection(self.mockroot)
        namespace = ["*"]
        print namespace
        host = "*"
        sel.select(namespace, host)

        count = len(self.mockhosts)
        result = sel.flatten()
        print result
        print len(result), count
        assert len(result) == count, \
        "The returned host differs in size from the expected"

    def test_no_namespace_all(self):
        """
        All hosts without Namespace are selected
        """
        sel = hostslist.HostSelection(self.mockroot)
        namespace = []
        host = "*"
        sel.select(namespace, host)
        count = 0
        for hst in self.mockhosts:
            if len(hst[0]) == 0:
                count += 1

        print count
        result = sel.flatten()
        print result
        print len(result), count
        assert len(result) == count, \
        "The returned host differs in size from the expected"

    def test_no_namespace_single(self):
        """
        A single Host with no namespoace is selected
        """
        sel = hostslist.HostSelection(self.mockroot)
        namespace = []
        host = "host22"
        sel.select(namespace, host)
        count = 0
        for hst in self.mockhosts:
            if len(hst[0]) == 0 and hst[1] == host:
                count += 1

        print count
        result = sel.flatten()
        print result
        print len(result), count
        assert len(result) == count, \
        "The returned host differs in size from the expected"

    def test_wildcard_exclude_hosts(self):
        """
        A list of hosts is excluded through wildcards
        """
        sel = hostslist.HostSelection(self.mockroot)
        for host in self.mockhosts:
            sel.select(host[0], host[1])
        namespace = self.mockhosts[3][0]
        host = "*"
        sel.exclude(namespace, host)

        count = len(self.mockhosts)
        for host in self.mockhosts:
            if cmp(host[0], namespace) == 0:
                count -= 1
        result = sel.flatten()
        print len(result), count
        assert len(result) == count, \
        "The returned host differs in size from the expected"

    def test_wildcard_exclude_namespace(self):
        """
        A list of namespaces is selected through wildcards
        """
        sel = hostslist.HostSelection(self.mockroot)
        for host in self.mockhosts:
            sel.select(host[0], host[1])
        namespace = self.mockhosts[3][0][:]
        namespace[-1] = "*"
        print namespace
        host = "*"
        sel.exclude(namespace, host)

        count = len(self.mockhosts)
        for host in self.mockhosts:
            if len(host[0]) == 0:
                pass
            elif host[0][0] == namespace[0] and host[0][1] == namespace[1]:
                print host[0], host[1]
                count -= 1
        result = sel.flatten()
        print result
        print len(result), count
        assert len(result) == count, \
        "The returned host differs in size from the expected"

    def test_wildcard_excl_fixed_host(self):
        """
        A list of namespaces is selected through wildcards
        with a fixed hostname
        """
        sel = hostslist.HostSelection(self.mockroot)
        for host in self.mockhosts:
            sel.select(host[0], host[1])
        namespace = self.mockhosts[3][0][:]
        namespace[-1] = "*"
        print namespace
        hst = "host3"
        sel.exclude(namespace, hst)

        count = len(self.mockhosts)
        for host in self.mockhosts:
            print host
            if len(host[0]) == 0:
                pass
            elif host[0][0] == namespace[0] and host[1] == hst:
                print host[0], host[1]
                count -= 1
        result = sel.flatten()
        print result
        print len(result), count
        assert len(result) == count, \
        "The returned host differs in size from the expected"

    def _comp_host(self, selection, expected_namespace, expected_host):
        """
        Helper function for test_parse_selection_positive
        """
        sel = HostSelection.parseSelection(selection)
        print sel[0], expected_namespace
        assert cmp(sel[0], expected_namespace) == 0, "The Namespace is wrong"
        print sel[1], expected_host
        assert sel[1] == expected_host, "The Host is wrong"

    def test_parse_selection_positive(self):
        """
        Parse the String pattern into a namespace and host selection
        """
        self._comp_host("/A1/b/C:host", ["a1", "b", "c"], "host")
        self._comp_host("/A/B/C", ["a", "b", "c"], "*")
        self._comp_host("/A/B/c:*", ["a", "b", "c"], "*")
        self._comp_host("/a/b/c:", ["a", "b", "c"], "*")
        self._comp_host("/A/B/*", ["a", "b", "*"], "*")
        self._comp_host("/A/B/*:host", ["a", "b", "*"], "host")
        self._comp_host("host", [], "host")
        self._comp_host("*", ["*"], "*")
        self._comp_host("*:host", ["*"], "host")
        self._comp_host("*:*", ["*"], "*")
        self._comp_host(":host", [], "host")

    def test_parse_selection_negative(self):
        """
        Parse the String pattern into a namespace and host selection
        """
        try:
            HostSelection.parseSelection("/A/B/C/:host")
            assert False, "There was supposed to be an exception"
        except hostslist.HostException:
            pass

        try:
            HostSelection.parseSelection("/A/B//C:host")
            assert False, "There was supposed to be an exception"
        except hostslist.HostException:
            pass

        try:
            HostSelection.parseSelection("/A/B /C:host")
            assert False, "There was supposed to be an exception"
        except hostslist.HostException:
            pass

    def test_integration(self):
        """
        everything
        """
        tmpfilename = "tmpfile"
        tmpfile = open(tmpfilename, 'w')
        for line in self.mockfile:
            tmpfile.write(line)
        tmpfile.close()
        tmpfile = open(tmpfilename, 'r')
        result = hostslist.select_hosts_from_file(tmpfile, "*;!host22").flatten()
        tmpfile.close()
        os.remove(tmpfilename)

        print result
        print len(self.mockhosts), len(result)
        assert len(result) == (len(self.mockhosts) - 1), \
        "Wrong number of hosts"
        assert "host22" not in result, "Excluded host found"
