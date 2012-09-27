from nose.tools import eq_
from fabric.state import _AliasDict
from fabric.io import _endswith, _get_prompt_response

def test_request_prompts():
    """
    Test valid responses from prompts
    """
    ad = _AliasDict(
        {'request_prompts' : { "prompt2" : "response2","prompt1" : "response1" } }
        )
    eq_(_get_prompt_response(list("this is a prompt for prompt1"),ad['request_prompts']),("prompt1","response1"))
    eq_(_get_prompt_response(list("this is a prompt for prompt2"),ad['request_prompts']),("prompt2","response2"))
