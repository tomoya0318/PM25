from constants import path
from utils.file_processor import list_files_in_directory, load_from_json, dump_to_json
from utils.ast_checker import are_ast_equal
from pattern.source_preprocessor import extract_diff
from pattern.converter import extract_trigger_sequence, extract_pattern_change
from pattern.source_preprocessor import variable_name_preprocessing
from tqdm import tqdm


def _contains_plus_and_minus(pattern):
    """パターンに`-`と`+`が同時に存在するかを確認する

    パターン内に変更を示す`-`（削除）と`+`（追加）が
    両方存在するかどうかをチェックする。

    Args:
        pattern (list): パターンのリスト

    Returns:
        bool: `-`と`+`が両方存在する場合はTrue、そうでない場合はFalse
    """
    contains_minus = any(token.startswith("-") for token in pattern)
    contains_plus = any(token.startswith("+") for token in pattern)
    return contains_minus and contains_plus


def _is_subpattern(small_pattern, big_pattern):
    small = set(small_pattern)
    big = set(big_pattern)
    return small.issubset(big)


def filter_patterns(patterns, patch_pairs, threshold=0.1):
    """パターンカウンターから指定された条件を満たさないパターンをフィルタリングする
        条件
        - 変更を提案しないコードの削除
        - 意味が重複するパターンの削除
        - 10%未満の信頼度のパターンを削除
        - 1度しか出現していないパターンを削除

    Args:
        patterns (set): パターンの集合
        patch_pairs (list): テストデータの変更前と変更後
        threshold (float, optional): _description_. Defaults to 0.1.

    Returns:
        _type_: _description_
    """
    filtered_patterns = []
    sorted_patterns = sorted(patterns, key=lambda x: -len(x[0]))

    for i, pattern in tqdm(enumerate(sorted_patterns), total=len(sorted_patterns), leave=False):
        # 変更を提案しないコード（`-`と`+`が同時に存在しないパターン）を削除
        if not _contains_plus_and_minus(pattern):
            continue

        # 重複する意味パターンを無視
        duplicate_found = False
        for larger_pattern in sorted_patterns[:i]:
            if _is_subpattern(pattern, larger_pattern):
                duplicate_found = True
                break
        if duplicate_found:
            continue

        # トリガーシーケンスを抽出
        trigger_sequence = extract_trigger_sequence(pattern)
        pattern_changed = extract_pattern_change(pattern)
        triggerable_initial = 0
        actually_changed = 0
        for condition, consequent in patch_pairs:
            condition = variable_name_preprocessing(condition)
            consequent = variable_name_preprocessing(consequent)
            if are_ast_equal(trigger_sequence, condition):
                triggerable_initial += 1
            if are_ast_equal(pattern_changed, consequent):
                actually_changed += 1

        # 信頼度を計算
        confidence = actually_changed / triggerable_initial if triggerable_initial > 0 else 0

        # 10%未満の信頼度のパターンを削除
        if confidence < threshold:
            continue

        # フィルタされたパターンを追加
        filtered_patterns.append({"pattern": pattern, "confidence": confidence})

    return filtered_patterns


if __name__ == "__main__":
    owner = "numpy"
    pattern_path = f"{path.INTERMEDIATE}/pattern/prefix/{owner}"
    test_path = f"{path.INTERMEDIATE}/test_data/{owner}"
    projects = list_files_in_directory(pattern_path)
    for project in projects:
        patterns = load_from_json(f"{pattern_path}/{project}")
        patterns = set([tuple(item["pattern"]) for item in patterns])
        patch_pairs = extract_diff(f"{test_path}/{project}")
        output_path = f"{path.INTERMEDIATE}/pattern/filtered/{owner}/{project}"

        filtered_patterns = filter_patterns(patterns, patch_pairs)
        dump_to_json(filtered_patterns, output_path)

# if __name__ == "__main__":
#     owner = "numpy"
#     pattern_path = f"{path.INTERMEDIATE}/pattern/prefix/{owner}"
#     test_path = f"{path.INTERMEDIATE}/test_data/{owner}"
#     projects = list_files_in_directory(pattern_path)

#     for project in projects:
#         patterns = load_from_json(f"{pattern_path}/{project}")
#         patterns = set([tuple(item['pattern']) for item in patterns])
#         patch_pairs = extract_diff(f"{test_path}/{project}")

#         filter_patterns(patterns, patch_pairs)
