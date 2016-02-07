# -*- coding: utf-8 -*-
import sys
from io import BytesIO

from nose.tools import eq_

from fabric.io import OutputLooper
from fabric.context_managers import hide, settings
from mock_streams import mock_streams


def test_request_prompts():
    """
    Test valid responses from prompts
    """
    def run(txt, prompts):
        with settings(prompts=prompts):
            # try to fulfil the OutputLooper interface, only want to test
            # _get_prompt_response. (str has a method upper)
            ol = OutputLooper(str, 'upper', None, list(txt), None)
            return ol._get_prompt_response()

    prompts = {"prompt2": "response2",
               "prompt1": "response1",
               "prompt": "response"
               }

    eq_(run("this is a prompt for prompt1", prompts), ("prompt1", "response1"))
    eq_(run("this is a prompt for prompt2", prompts), ("prompt2", "response2"))
    eq_(run("this is a prompt for promptx:", prompts), (None, None))
    eq_(run("prompt for promp", prompts), (None, None))


@mock_streams('stdout')
def test_pip_progressbar_at_4096_byte_boundary_error():
    """
    Test for unicode characters from the pip installation progress bar
    causing a UnicodeDecodeError.
    """
    expect = '█' * 4096

    class Mock(object):
        def __init__(self):
            three_bytes = u'█'.encode('utf-8')
            # 4096 comes from OutputLooper.read_size being hard-coded to 4096
            self.source = BytesIO(three_bytes * 4096)

        def get_unicode_bytes(self, size):
            return self.source.read(size)

    ol = OutputLooper(Mock(), 'get_unicode_bytes', sys.stdout, None, None)

    with settings(hide('everything')):
        ol.loop()
    eq_(expect, sys.stdout.getvalue())
