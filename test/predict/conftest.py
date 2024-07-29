import pytest
from collections import Counter

@pytest.fixture
def pattern_data():
    pattern = {
        "('=i=dic', '-[', '+.get(', '=STRING', '-]', '+)')": 2,
        "('=i=dic', '-[', '+.get(', ='NUMBER', '-]', '+)')": 2
    }
    return pattern