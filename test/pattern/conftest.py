import pytest


@pytest.fixture
def diff_data():
    return {"condition": "i = dic[STRING]", "consequent": "i = dic.get(STRING)"}


@pytest.fixture
def tokens1():
    return ["=i=dic", "-[", "+.get(", "=STRING", "-]", "+)"]


@pytest.fixture
def tokens2():
    return ["=i=dic", "-[", "+.get(", "=STRING", "-]", "+)", "+get(STRING)"]
