# -*- coding: utf-8 -*-
from __future__ import with_statement

import os

from fabric.api import hide, get, show
from fabric.contrib.files import upload_template, contains

from utils import FabricTest, eq_contents
from server import server


class TestContrib(FabricTest):
    # Make sure it knows / is a directory.
    # This is in lieu of starting down the "actual honest to god fake operating
    # system" road...:(
    @server(responses={'test -d "$(echo /)"': ""})
    def test_upload_template_uses_correct_remote_filename(self):
        """
        upload_template() shouldn't munge final remote filename
        """
        template = self.mkfile('template.txt', 'text')
        with hide('everything'):
            upload_template(template, '/')
            assert self.exists_remotely('/template.txt')

    @server()
    def test_upload_template_handles_file_destination(self):
        """
        upload_template() should work OK with file and directory destinations
        """
        template = self.mkfile('template.txt', '%(varname)s')
        local = self.path('result.txt')
        remote = '/configfile.txt'
        var = 'foobar'
        with hide('everything'):
            upload_template(template, remote, {'varname': var})
            get(remote, local)
        eq_contents(local, var)

    @server(responses={
        'egrep "text" "/file.txt"': (
            "sudo: unable to resolve host fabric",
            "",
            1
        )}
    )
    def test_contains_checks_only_succeeded_flag(self):
        """
        contains() should return False on bad grep even if stdout isn't empty
        """
        with hide('everything'):
            result = contains('/file.txt', 'text', use_sudo=True)
            assert result == False

    @server()
    def test_upload_template_handles_jinja_template(self):
        """
        upload_template() should work OK with Jinja2 template
        """
        template = self.mkfile('template_jinja2.txt', '{{ first_name }}')
        template_name = os.path.basename(template)
        template_dir = os.path.dirname(template)
        local = self.path('result.txt')
        remote = '/configfile.txt'
        first_name = u'S\u00E9bastien'
        with hide('everything'):
            upload_template(template_name, remote, {'first_name': first_name},
                use_jinja=True, template_dir=template_dir)
            get(remote, local)
        eq_contents(local, first_name.encode('utf-8'))

    @server()
    def test_upload_template_jinja_and_no_template_dir(self):
        # Crummy doesn't-die test
        fname = "foo.tpl"
        try:
            with hide('everything'):
                with open(fname, 'w+') as fd:
                    fd.write('whatever')
                upload_template(fname, '/configfile.txt', {}, use_jinja=True)
        finally:
            os.remove(fname)
