# -*- coding: utf-8 -*-
from __future__ import with_statement
from fabric.operations import local
import os

from fabric.api import hide, get, show
from fabric.contrib.files import upload_template, contains, _escape_for_regex
from fabric.context_managers import lcd

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

    @server()
    def test_upload_template_handles_template_dir(self):
        """
        upload_template() should work OK with template dir
        """
        template = self.mkfile('template.txt', '%(varname)s')
        template_dir = os.path.dirname(template)
        local = self.path('result.txt')
        remote = '/configfile.txt'
        var = 'foobar'
        with hide('everything'):
            upload_template(
                'template.txt', remote, {'varname': var},
                template_dir=template_dir
            )
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


    def test_upload_template_obeys_lcd(self):
        for jinja in (True, False):
            for mirror in (True, False):
                self._upload_template_obeys_lcd(jinja=jinja, mirror=mirror)

    @server()
    def _upload_template_obeys_lcd(self, jinja, mirror):
        template_content = {True: '{{ varname }}s', False: '%(varname)s'}

        template_dir = 'template_dir'
        template_name = 'template.txt'
        if not self.exists_locally(self.path(template_dir)):
            os.mkdir(self.path(template_dir))

        self.mkfile(
            os.path.join(template_dir, template_name), template_content[jinja]
        )

        remote = '/configfile.txt'
        var = 'foobar'
        with hide('everything'):
            with lcd(self.path(template_dir)):
                upload_template(
                    template_name, remote, {'varname': var},
                    mirror_local_mode=mirror
                )

    def test_escape_for_regex_allows_pipes(self):
        valid = {
            r"cat file1 > file2": r'cat\ file1 > file2',
            r"cat file2 >> file3": r'cat\ file2 >> file3',
            r"ls > dirlist 2>&1": r'ls > dirlist\ 2\>\&1',
            r"<html><head></head><body>":r'\<html\>\<head\>\<\/head\>\<body\>',
            r"Mailto: <cmattoon@cmattoon.com>": r'Mailto\:\ \<cmattoon\@cmattoon\.com\>',
            r"cat file3 | more": r'cat\ file3 | more'
            }

        for (text, expected) in valid.iteritems():
            assert expected == _escape_for_regex(text)
        





        
