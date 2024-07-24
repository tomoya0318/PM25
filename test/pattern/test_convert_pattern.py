import pytest
from collections import Counter
from pattern.convert_code_into_pattern import (
    compute_token_diff,
    merge_consecutive_tokens,
    extract_valid_subsequences,
    extract_trigger_sequence,
    update_pattern_counter,
    filter_patterns,
    process_patch_pairs,
)

@pytest.fixture
def diff_data():
    return {"condition": "i = dic[STRING]", "consequent": "i = dic.get(STRING)"}


@pytest.fixture
def tokens1():
    return ["=i=dic", "-[", "+.get(", "=STRING", "-]", "+)"]


@pytest.fixture
def tokens2():
    return ["=i=dic", "-[", "+.get(", "=STRING", "-]", "+)", "+get(STRING)"]


def test_sequence_token_diff(diff_data):
    expected_diff = ["=i=dic", "-[", "+.get(", "=STRING", "-]", "+)"]
    diff = compute_token_diff(diff_data["condition"], diff_data["consequent"])
    output_diff = merge_consecutive_tokens(diff)
    assert output_diff == expected_diff


def test_extract_valid_subsequences(tokens1):
    expected_patterns = Counter(
        {
            ("=i=dic", "-["): 1,
            ("=i=dic", "+.get("): 1,
            ("=i=dic", "-]"): 1,
            ("=i=dic", "+)"): 1,
            ("=i=dic", "-[", "+.get("): 1,
            ("=i=dic", "-[", "=STRING"): 1,
            ("=i=dic", "-[", "-]"): 1,
            ("=i=dic", "-[", "+)"): 1,
            ("=i=dic", "+.get(", "=STRING"): 1,
            ("=i=dic", "+.get(", "-]"): 1,
            ("=i=dic", "+.get(", "+)"): 1,
            ("=i=dic", "=STRING", "-]"): 1,
            ("=i=dic", "=STRING", "+)"): 1,
            ("=i=dic", "-]", "+)"): 1,
            ("=i=dic", "-[", "+.get(", "=STRING"): 1,
            ("=i=dic", "-[", "+.get(", "-]"): 1,
            ("=i=dic", "-[", "+.get(", "+)"): 1,
            ("=i=dic", "-[", "=STRING", "-]"): 1,
            ("=i=dic", "-[", "=STRING", "+)"): 1,
            ("=i=dic", "-[", "-]", "+)"): 1,
            ("=i=dic", "+.get(", "=STRING", "-]"): 1,
            ("=i=dic", "+.get(", "=STRING", "+)"): 1,
            ("=i=dic", "+.get(", "-]", "+)"): 1,
            ("=i=dic", "=STRING", "-]", "+)"): 1,
            ("=i=dic", "-[", "+.get(", "=STRING", "-]"): 1,
            ("=i=dic", "-[", "+.get(", "=STRING", "+)"): 1,
            ("=i=dic", "-[", "+.get(", "-]", "+)"): 1,
            ("=i=dic", "-[", "=STRING", "-]", "+)"): 1,
            ("=i=dic", "+.get(", "=STRING", "-]", "+)"): 1,
            ("=i=dic", "-[", "+.get(", "=STRING", "-]", "+)"): 1,
        }
    )
    patterns = extract_valid_subsequences(tokens1)
    assert patterns == expected_patterns


def test_extract_trigger_sequence(tokens1):
    except_diff = ("=i=dic", "-[", "=STRING", "-]")
    output_diff = extract_trigger_sequence(tokens1)
    assert output_diff == except_diff


def test_update_pattern_counter(tokens1, tokens2):
    expected_patterns = Counter(
        {
            ("=i=dic", "-["): 2,
            ("=i=dic", "+.get("): 2,
            ("=i=dic", "-]"): 2,
            ("=i=dic", "+)"): 2,
            ("=i=dic", "-[", "+.get("): 2,
            ("=i=dic", "-[", "=STRING"): 2,
            ("=i=dic", "-[", "-]"): 2,
            ("=i=dic", "-[", "+)"): 2,
            ("=i=dic", "+.get(", "=STRING"): 2,
            ("=i=dic", "+.get(", "-]"): 2,
            ("=i=dic", "+.get(", "+)"): 2,
            ("=i=dic", "=STRING", "-]"): 2,
            ("=i=dic", "=STRING", "+)"): 2,
            ("=i=dic", "-]", "+)"): 2,
            ("=i=dic", "-[", "+.get(", "=STRING"): 2,
            ("=i=dic", "-[", "+.get(", "-]"): 2,
            ("=i=dic", "-[", "+.get(", "+)"): 2,
            ("=i=dic", "-[", "=STRING", "-]"): 2,
            ("=i=dic", "-[", "=STRING", "+)"): 2,
            ("=i=dic", "-[", "-]", "+)"): 2,
            ("=i=dic", "+.get(", "=STRING", "-]"): 2,
            ("=i=dic", "+.get(", "=STRING", "+)"): 2,
            ("=i=dic", "+.get(", "-]", "+)"): 2,
            ("=i=dic", "=STRING", "-]", "+)"): 2,
            ("=i=dic", "-[", "+.get(", "=STRING", "-]"): 2,
            ("=i=dic", "-[", "+.get(", "=STRING", "+)"): 2,
            ("=i=dic", "-[", "+.get(", "-]", "+)"): 2,
            ("=i=dic", "-[", "=STRING", "-]", "+)"): 2,
            ("=i=dic", "+.get(", "=STRING", "-]", "+)"): 2,
            ("=i=dic", "-[", "+.get(", "=STRING", "-]", "+)"): 2,
            ("=i=dic", "+get(STRING)"): 1,
            ("=i=dic", "-[", "+get(STRING)"): 1,
            ("=i=dic", "+.get(", "+get(STRING)"): 1,
            ("=i=dic", "=STRING", "+get(STRING)"): 1,
            ("=i=dic", "-]", "+get(STRING)"): 1,
            ("=i=dic", "+)", "+get(STRING)"): 1,
            ("=i=dic", "-[", "+.get(", "+get(STRING)"): 1,
            ("=i=dic", "-[", "=STRING", "+get(STRING)"): 1,
            ("=i=dic", "-[", "-]", "+get(STRING)"): 1,
            ("=i=dic", "-[", "+)", "+get(STRING)"): 1,
            ("=i=dic", "+.get(", "=STRING", "+get(STRING)"): 1,
            ("=i=dic", "+.get(", "-]", "+get(STRING)"): 1,
            ("=i=dic", "+.get(", "+)", "+get(STRING)"): 1,
            ("=i=dic", "=STRING", "-]", "+get(STRING)"): 1,
            ("=i=dic", "=STRING", "+)", "+get(STRING)"): 1,
            ("=i=dic", "-]", "+)", "+get(STRING)"): 1,
            ("=i=dic", "-[", "+.get(", "=STRING", "+get(STRING)"): 1,
            ("=i=dic", "-[", "+.get(", "-]", "+get(STRING)"): 1,
            ("=i=dic", "-[", "+.get(", "+)", "+get(STRING)"): 1,
            ("=i=dic", "-[", "=STRING", "-]", "+get(STRING)"): 1,
            ("=i=dic", "-[", "=STRING", "+)", "+get(STRING)"): 1,
            ("=i=dic", "-[", "-]", "+)", "+get(STRING)"): 1,
            ("=i=dic", "+.get(", "=STRING", "-]", "+get(STRING)"): 1,
            ("=i=dic", "+.get(", "=STRING", "+)", "+get(STRING)"): 1,
            ("=i=dic", "+.get(", "-]", "+)", "+get(STRING)"): 1,
            ("=i=dic", "=STRING", "-]", "+)", "+get(STRING)"): 1,
            ("=i=dic", "-[", "+.get(", "=STRING", "-]", "+get(STRING)"): 1,
            ("=i=dic", "-[", "+.get(", "=STRING", "+)", "+get(STRING)"): 1,
            ("=i=dic", "-[", "+.get(", "-]", "+)", "+get(STRING)"): 1,
            ("=i=dic", "-[", "=STRING", "-]", "+)", "+get(STRING)"): 1,
            ("=i=dic", "+.get(", "=STRING", "-]", "+)", "+get(STRING)"): 1,
            ("=i=dic", "-[", "+.get(", "=STRING", "-]", "+)", "+get(STRING)"): 1,
        }
    )

    pattern_counter = extract_valid_subsequences(tokens1)
    update_pattern_counter(pattern_counter, tokens2)

    assert pattern_counter == expected_patterns


def test_filter_patterns():
    pattern_counter = Counter(
        {
            ("=i=dic", "-[", "+.get(", "=STRING", "-]", "+)"): 2,
            ("=x=y", "-+", "+*", "=z"): 1,
            ("=foo=", "-bar()", "+baz()"): 1,
            ("=i=dic", "-[", "=VAR", "-]"): 3,
        }
    )

    triggerable_initial = Counter(
        {("=i=dic", "-[", "=STRING", "-]"): 3, ("=x=y", "-+", "=z"): 2, ("=foo=", "-bar()"): 2}
    )

    actually_changed = Counter(
        {
            ("=i=dic", "-[", "+.get(", "=STRING", "-]", "+)"): 2,
            ("=x=y", "-+", "+*", "=z"): 1,
            ("=foo=", "-bar()", "+baz()"): 1,
            ("=i=dic", "-[", "=VAR", "-]"): 3,
        }
    )

    expected_filtered_patterns = Counter({("i=dic", "-[", "+.get(", "STRING", "-]", "+)"): 2})

    filtered_patterns = filter_patterns(pattern_counter, triggerable_initial, actually_changed, threshold=0.1)

    assert filtered_patterns == expected_filtered_patterns


def test_process_patch_pairs():
    patch_pairs = [
        ("i = dic[STRING]", "i = dic.get(STRING)"),
        ("i = dic[STRING]", "i = dic.get(STRING)"),
        ("x = y + z", "x = y * z"),
        ("foo = bar()", "foo = baz()"),
    ]
    expected_pattern = Counter({("i=dic", "-[", "+.get(", "STRING", "-]", "+)"): 2})
    pattern = process_patch_pairs(patch_pairs)
    assert pattern == expected_pattern
