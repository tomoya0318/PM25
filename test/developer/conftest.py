import pytest
import json
from constants import path
from utils.file_processor import ensure_dir_exists, remove_dir

@pytest.fixture
def developers_set_1():
    """テスト用の開発者集合1を提供するフィクスチャ"""
    return {
        "Alice",
        "Bob",
        "Charlie",
        "David"
    }

@pytest.fixture
def developers_set_2():
    """テスト用の開発者集合2を提供するフィクスチャ"""
    return {
        "Charlie",
        "David",
        "Eve",
        "Frank"
    }

@pytest.fixture
def tmp_json_file():
    """一時的なJSONファイルを含むディレクトリを作成し、テスト終了後に削除するフィクスチャ"""
    dir_path = path.TMP
    file_path = f"{path.TMP}/test_data.json"
    ensure_dir_exists(file_path)
    
    data = [
        {"author": "Alice"},
        {"author": "Bob"},
        {"author": "Charlie"},
        {"author": "David"},
    ]
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    
    yield file_path  # ここで一時ディレクトリのパスを返す

    remove_dir(dir_path)
