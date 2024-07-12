import pytest
from collections import Counter
from pattern.convert_code_into_pattern import compute_token_diff, merge_consecutive_tokens, extract_valid_subsequences, update_pattern_counter

@pytest.fixture
def diff_data():
    return {
        "condition": "i = dic",
        "consequent": "i = dic.get"
    }

@pytest.fixture
def tokens1():
    return ['i=dic', '-[']

@pytest.fixture
def tokens2():
    return ['i=dic', '-[', '+.get']

def test_sequence_token_diff(diff_data):
    expected_diff = ['i=dic', '+.get']
    diff = compute_token_diff(diff_data["condition"], diff_data["consequent"])
    output_diff = merge_consecutive_tokens(diff)
    assert output_diff == expected_diff

def test_extract_valid_subsequences(tokens1):
    expected_patterns = Counter({
        ('i=dic','-['): 1,
    })
    patterns = extract_valid_subsequences(tokens1)
    assert patterns == expected_patterns

def test_update_pattern_counter(tokens1, tokens2):
    expected_patterns = Counter({
        ('i=dic','-['): 2,
        ('i=dic','-[', '+.get'): 1,
        ('i=dic', '+.get'): 1,
    })
    
    pattern_counter = extract_valid_subsequences(tokens1)
    update_pattern_counter(pattern_counter, tokens2)
    
    assert pattern_counter == expected_patterns
