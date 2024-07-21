import os
from collections import Counter
from convert_code_into_pattern import (
    compute_token_diff,
    merge_consecutive_tokens,
    extract_valid_subsequences,
    extract_trigger_sequence,
    update_pattern_counter,
    filter_patterns,
)
from source_preprocessor import extract_diff

if __name__ == "__main__":
    # JSONファイルのパス
    json_file_path = os.path.join(os.path.dirname(__file__), "../../data/sample_data.json")

    # JSONファイルから初期パッチと統合パッチを抽出
    patch_pairs = extract_diff(json_file_path)
    # パターンカウンターとトリガーシーケンスカウンターを初期化
    pattern_counter = Counter()
    triggerable_initial = Counter()
    actually_changed = Counter()

    # 各例について差分を計算し、パターンカウンターを更新
    for condition, consequent in patch_pairs:
        diff_tokens = compute_token_diff(condition, consequent)
        if not diff_tokens:
            continue
        merged_diff_tokens = merge_consecutive_tokens(diff_tokens)
        new_patterns = extract_valid_subsequences(merged_diff_tokens)
        update_pattern_counter(pattern_counter, merged_diff_tokens)

        for pattern in new_patterns:
            trigger_sequence = extract_trigger_sequence(pattern)
            triggerable_initial[trigger_sequence] += new_patterns[pattern]
            actually_changed[pattern] += new_patterns[pattern]

    # パターンの信頼度をフィルタリング
    filtered_patterns = filter_patterns(pattern_counter, triggerable_initial, actually_changed, threshold=0.1)

    # 抽出された有効な部分列とその頻度を表示
    for subseq, count in filtered_patterns.items():
        print(
            f"Pattern: {subseq},"
            f"Count: {count},"
            f"Confidence: {actually_changed[subseq] / triggerable_initial[extract_trigger_sequence(subseq)]:.2f}"
        )
