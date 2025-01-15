from tqdm import tqdm
from pathlib import Path
from constants import path
from pattern.diff2sequence import merge_consecutive_tokens
from utils.file_processor import load_from_json, dump_to_json


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


def is_short_pattern(pattern: list[str], length: int) -> bool:
    if len(pattern) <= length:
        return False
    return True


def process_all_pattern(patterns_path: Path, output_path: Path):
    pattern_data_list = load_from_json(patterns_path)

    #昇順で並び替え
    sorted(pattern_data_list, key=lambda x: x["support"], reverse=True)

    # 冗長なパターンを削除
    filtered_patterns = [
        (merge_consecutive_tokens(pattern_data["pattern"]), pattern_data["support"])
        for pattern_data in pattern_data_list
        if is_short_pattern(pattern_data["pattern"], 4)
    ]

    dump_to_json(filtered_patterns, output_path)


if __name__ == "__main__":
    owner = "openstack"
    repo = "neutron"
    diff_path = path.RESOURCE / owner / f"{repo}.json"
    patterns_path = path.RESULTS / owner / "2013to2014"/ f"{repo}.json"
    out_path = path.RESULTS / owner / "2013to2014"/f"filtered_{repo}.json"

    process_all_pattern(patterns_path, out_path)
