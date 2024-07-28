import pytest
import json
from constants import path
from utils.file_processor import ensure_dir_exists, remove_dir
from developer.preprocessor import (
    extract_author,
    save_author_to_json
)

def test_extract_author(tmp_json_file, developers_set_1):
    authors = extract_author(tmp_json_file)
    assert authors == developers_set_1

def test_save_author_to_json(developers_set_1):
    save_dir = path.TMP
    ensure_dir_exists(save_dir)
    save_path = f"{save_dir}/test_output.json"
    save_author_to_json(developers_set_1, save_path)

    with open(save_path, "r", encoding="utf-8") as f:
        saved_authors = set(json.load(f))

    assert saved_authors == developers_set_1

    remove_dir(save_dir)