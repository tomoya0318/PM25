import pytest
from pattern.convert_code_into_pattern import compute_token_diff

@pytest.fixture
def condition():
    return "i=dic[STRING]"

@pytest.fixture
def consequent():
    return "i=dic.get(STRING)"

def test_compute_token_diff(condition, consequent):
    expected_diff = ['i', '=', 'dic', '-[', '+.', '+get', '+(', "STRING", '-]', '+)']
    diff = compute_token_diff(condition, consequent)
    assert diff == expected_diff