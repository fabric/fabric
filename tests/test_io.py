from __future__ import with_statement

from nose.tools import eq_

from fabric.io import OutputLooper
from fabric.context_managers import settings


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
