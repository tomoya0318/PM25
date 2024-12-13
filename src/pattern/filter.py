from tqdm import tqdm
from pathlib import Path
from constants import path
from pattern.diff2sequence import extract_diff, merge_consecutive_tokens
from utils.file_processor import load_from_json, dump_to_json


def calc_confidence(pattern: list[str], diff_path: Path) -> float:
    triggerable_count = 0
    actually_changed_count = 0

    for _, diff_hunk in extract_diff(diff_path):
        if _is_trigger_sequence(pattern, diff_hunk.condition):
            triggerable_count += 1
            if _is_actually_chnage(pattern, diff_hunk.consequent):
                actually_changed_count += 1

    if triggerable_count == 0:
        return 0.0

    return round(actually_changed_count / triggerable_count, 2)


def _is_trigger_sequence(pattern: list[str], condition: list[str]) -> bool:
    """パターンが適用可能か判定"""
    trigger = [token.lstrip("-=") for token in pattern if token.startswith("-") or token.startswith("=")]
    if not trigger:
        return False

    before_code = "".join(condition)

    for t in trigger:
        if t not in before_code:
            return False

    return True


def _is_actually_chnage(pattern: list[str], consequent: list[str]) -> bool:
    """パターンによる変更があるか判定"""
    actually_change = [token.lstrip("+=") for token in pattern if token.startswith("+") or token.startswith("=")]
    if not actually_change:
        return False

    after_code = "".join(consequent)
    for change in actually_change:
        if change not in after_code:
            return False

    return True


def remove_subset_patterns(patterns: list[list[str]]) -> list[list[str]]:
    """部分的に重複するパターンを削除"""
    # パターンを長さ順に降順ソート
    patterns.sort(key=lambda x: sum(len(token) for token in x), reverse=True)

    unique_patterns = []
    print("start remove")
    for pattern in tqdm(patterns):
        if not any(all(token in " ".join(other) for token in pattern) for other in unique_patterns):
            unique_patterns.append(pattern)
    return unique_patterns


def process_all_pattern(diff_path: Path, patterns_path: Path, output_path: Path):
    patterns = load_from_json(patterns_path)

    # パターンをキー、サポート値を値とする辞書を作成
    pattern_support_map = {tuple(p["pattern"]): p["support"] for p in patterns}
    # 冗長なパターンを削除
    filtered_patterns = remove_subset_patterns([pattern["pattern"] for pattern in patterns])

    result = []
    for pattern in filtered_patterns:
        confidence = calc_confidence(pattern, diff_path)
        if confidence <= 0.10:
            continue
        result.append(
            {
                "pattern": merge_consecutive_tokens(pattern),
                "support": pattern_support_map[tuple(pattern)],
                "confidence": confidence,
            }
        )
    dump_to_json(result, output_path)


if __name__ == "__main__":
    owner = "numpy"
    repo = "numpy"
    diff_path = path.RESOURCE/owner/f"{repo}.json"
    patterns_path = path.RESULTS/owner/f"{repo}.json"
    out_path = path.RESULTS/owner/f"filtered_{repo}.json"

    process_all_pattern(diff_path, patterns_path, out_path)
