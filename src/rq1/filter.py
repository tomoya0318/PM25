from itertools import chain
from pathlib import Path

from joblib import Parallel, delayed
from tqdm import tqdm

from constants import path
from models.pattern import PatternWithSupport
from pattern.merge import merge_pattern_results
from utils.file_processor import load_from_json, dump_to_json
from utils.discord import send_discord_notification


def is_subsequence(sub: list[str], seq: list[str]) -> bool:
    """`sub` が `seq` の順序を保った部分列であるかを確認"""
    it = iter(seq)
    return all(token in it for token in sub)


def remove_subset_patterns(patterns: list[PatternWithSupport]) -> list[PatternWithSupport]:
    """順序を考慮して部分的に重複するパターンを削除"""
    # パターンを長さ順に降順ソート
    patterns.sort(key=lambda x: sum(len(token) for token in x.pattern), reverse=True)

    unique_patterns = []
    print("start remove")
    for pattern in tqdm(patterns):
        if not any(is_subsequence(pattern.pattern, other.pattern) for other in unique_patterns):
            unique_patterns.append(PatternWithSupport(pattern.pattern, pattern.support))
    return unique_patterns


def is_long_pattern(pattern: list[str], length: int) -> bool:
    if len(pattern) <= length:
        return False
    return True


def single_process(base_path: Path, year: int) -> list[PatternWithSupport]:
    input_path = base_path / f"{year}to{year + 1}" / "nova.json"
    output_path = base_path / f"{year}to{year + 1}" / "filtered_nova.json"

    # パターンの読み込み
    data = load_from_json(input_path)
    patterns = [PatternWithSupport.from_dict(item) for item in data]

    # 部分パターンを削除
    unique_patterns = remove_subset_patterns(patterns)

    # 保存
    unique_data = [pattern.to_dict() for pattern in unique_patterns]
    dump_to_json(unique_data, output_path)

    return unique_patterns


def parallel_process(base_path, start_year, end_year):
    output_path = base_path / "all" / "merged_nova.json"
    results = Parallel(n_jobs=-1, verbose=10)(
        delayed(single_process)(base_path, year) for year in range(start_year, end_year)
    )
    send_discord_notification("パターンのフィルタリングが完了しました。")

    flat_results: list[PatternWithSupport] = list(chain.from_iterable(results))  # type: ignore

    merged_patterns = merge_pattern_results(flat_results)
    send_discord_notification("パターンの統合が完了しました。")

    remove_subset_patterns(merged_patterns)
    # 保存
    unique_data = [pattern.to_dict() for pattern in merged_patterns]
    dump_to_json(unique_data, output_path)


if __name__ == "__main__":
    start_year = 2017
    end_year = 2025

    base_path = path.RESULTS / "openstack"
    parallel_process(base_path, start_year, end_year)
