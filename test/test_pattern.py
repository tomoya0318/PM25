import pytest
import sys
import os
sys.path.append("../")
from src.pattern.convert_code_into_pattern import variable_name_preprocessing, tokenize_python_code
@pytest.fixture
def some_data():
    #テスト用のコード
    code = """
    class ${0:NAME}:
    """
    yield code

def test_variable_name_preprocessing(some_data):
    processed_code = variable_name_preprocessing(some_data)
    tokenized_code = tokenize_python_code(processed_code)
    ans = ['class', 'NAME', ':']
    assert ans == tokenized_code