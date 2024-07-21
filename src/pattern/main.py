import os
from convert_code_into_pattern import process_patch_pairs

from source_preprocessor import extract_diff

if __name__ == "__main__":
    # JSONファイルのパス
    json_file_path = os.path.join(os.path.dirname(__file__), "../../data/sample_data.json")

    # JSONファイルから初期パッチと統合パッチを抽出
    patch_pairs = extract_diff(json_file_path)
    filtered_patterns = process_patch_pairs(patch_pairs)
    for subseq, count in filtered_patterns.items():
        print(f"Pattern: {subseq}," f"Count: {count},")
