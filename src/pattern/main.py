import os
from constants import path
from pattern.converter import process_patch_pairs
from pattern.source_preprocessor import extract_diff, save_patterns_to_json

if __name__ == "__main__":
    # JSONファイルのパス
    json_file_path = f"{path.RESOURCE}/sample_data.json"
    # json_file_path = f"{path.RESOURCE}/numpy_numpy_Python_master.json"
    output_path = f"{path.INTERMEDIATE}/pattern/sample_patterns.json"
    # output_path = f"{path.INTERMEDIATE}/pattern/numpy_numpy_Python_master.json"

    # JSONファイルから初期パッチと統合パッチを抽出
    patch_pairs = extract_diff(json_file_path)
    filtered_patterns = process_patch_pairs(patch_pairs)
    save_patterns_to_json(filtered_patterns, output_path)
