import pytest
from pattern.convert_code_into_pattern import compute_token_diff, merge_consecutive_tokens

@pytest.fixture
def condition():
    return "i=dic[STRING]"

@pytest.fixture
def consequent():
    return "i=dic.get(STRING)"

def test_sequence_token_diff(condition, consequent):
    expected_diff = ['i=dic', '-[', '+.get(', 'STRING', '-]', '+)']
    diff = compute_token_diff(condition, consequent)

    assert merge_consecutive_tokens(diff) == expected_diff