import pytest
import os
import json

from pattern.code2diff.source_preprocessor import variable_name_preprocessing, tokenize_python_code, extract_diff


@pytest.fixture
def some_data():
    # テスト用のコード
    code = """
    class ${0:NAME}:
    """
    yield code


@pytest.fixture
def json_test_data():
    # テスト用のJSONデータ
    test_data = [
        {
            "repository": "numpy/numpy",
            "number": 26229,
            "sha": "12fd2d1b073c1a93e7d6fe23ce27651652779d1a",
            "author": "ngoldbaum",
            "created_at": "2024-04-08 18:39:40",
            "condition": ["${0:STRING}, ${1:STRING}, '_SUPPORTS_SVE'"],
            "consequent": ["${0:STRING}, ${1:STRING}, '_SUPPORTS_SVE', 'NOGIL_BUILD'"],
        },
        {
            "repository": "numpy/numpy",
            "number": 26229,
            "sha": "12fd2d1b073c1a93e7d6fe23ce27651652779d1a",
            "author": "ngoldbaum",
            "created_at": "2024-04-08 18:39:40",
            "condition": ['sysconfig.get_config_var("Py_GIL_DISABLED"),'],
            "consequent": ["NOGIL_BUILD,"],
        },
    ]
    # 一時ファイルに書き込む
    with open("test_data.json", "w") as file:
        json.dump(test_data, file)
    yield "test_data.json"
    # テスト終了後にファイルを削除
    os.remove("test_data.json")


# 前処理のテスト用
def test_variable_name_preprocessing(some_data):
    processed_code = variable_name_preprocessing(some_data)
    tokenized_code = tokenize_python_code(processed_code)
    ans = ["class", "NAME", ":"]
    assert ans == tokenized_code


# jsonファイルからconditionとconsequentを読み込めるかのテスト
def test_extract_diff(json_test_data):
    expected_output = [
        ["${0:STRING}, ${1:STRING}, '_SUPPORTS_SVE'", "${0:STRING}, ${1:STRING}, '_SUPPORTS_SVE', 'NOGIL_BUILD'"],
        ['sysconfig.get_config_var("Py_GIL_DISABLED"),', "NOGIL_BUILD,"],
    ]
    assert extract_diff(json_test_data) == expected_output
