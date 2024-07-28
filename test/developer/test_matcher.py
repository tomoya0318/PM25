import pytest
from developer.matcher import (
    calc_match_rate
)

def test_calc_match_rate(developers_set_1, developers_set_2):
    match_rate = calc_match_rate(developers_set_1, developers_set_2)
    expected_rate = 2 / 6
    assert match_rate == expected_rate