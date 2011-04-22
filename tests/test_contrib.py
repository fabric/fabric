from __future__ import with_statement

from fabric.contrib.files import upload_template

from utils import FabricTest
from server import server

class TestContrib(FabricTest):
    @server()
    def test_upload_template_uses_correct_remote_filename(self):
        """
        upload_template() shouldn't munge final remote filename
        """
        template = self.mkfile('template.txt', 'text')
        upload_template(template, '/')
        assert self.exists_remotely('/template.txt')
