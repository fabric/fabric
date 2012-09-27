from nose.tools import eq_
from fabric.state import _AliasDict
from fabric.io import _endswith, _get_prompt_response

def test_request_prompts():
    """
    Test valid responses from prompts
    """
    ad = _AliasDict(
    {'request_prompts' : { "prompt2" : "response2","prompt1" : "response1" ,"prompt": "response" } }
        )
    eq_(_get_prompt_response(list("this is a prompt for prompt1"),ad['request_prompts']),("prompt1","response1"))
    eq_(_get_prompt_response(list("this is a prompt for prompt2"),ad['request_prompts']),("prompt2","response2"))
    eq_(_get_prompt_response(list("this is a prompt for promptx:"),ad['request_prompts']),None)
    eq_(_get_prompt_response(list("prompt for prom:"),ad['request_prompts']),None)
