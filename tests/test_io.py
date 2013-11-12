from nose.tools import eq_
from fabric.state import _AliasDict
from fabric.io import OutputLooper
from fabric.state import env


def test_request_prompts():
    """
    Test valid responses from prompts
    """
    def run(txt, responses):
        # try to fulfil the OutputLooper interface, only want to test
        # _get_prompt_response.
        old, env.prompt_responses = env.prompt_responses, responses
        try:
            ol = OutputLooper(int, 'real', None, list(txt), None)
            return ol._get_prompt_response()
        finally:
            env.prompt_responses = old

    ad = _AliasDict({
        'prompt_responses': {
            "prompt2": "response2",
            "prompt1": "response1",
            "prompt": "response"
        }
    })
    eq_(run("this is a prompt for prompt1", ad['prompt_responses']), ("prompt1","response1"))
    eq_(run("this is a prompt for prompt2", ad['prompt_responses']), ("prompt2","response2"))
    eq_(run("this is a prompt for promptx:", ad['prompt_responses']), None)
    eq_(run("prompt for promp", ad['prompt_responses']), None)
