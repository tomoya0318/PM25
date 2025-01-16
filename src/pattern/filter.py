from tqdm import tqdm

from joblib import Parallel, delayed
from pathlib import Path
from itertools import chain, groupby

from constants import path
from models.pattern import PatternWithSupport
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


def process_single_repo_year(input_path: Path) -> list[PatternWithSupport]:
    if not input_path.exists():
        print(f"{input_path} is not exist")
        return []

    pattern_data_list = [
        PatternWithSupport.from_dict(item) for item in load_from_json(input_path)
    ]

    # 冗長なパターンを削除
    filtered_patterns = [
        PatternWithSupport(merge_consecutive_tokens(pattern_data.pattern), pattern_data.support)
        for pattern_data in pattern_data_list
        if is_short_pattern(pattern_data.pattern, 4)
    ]

    return filtered_patterns


def merge_pattern_results(pattern_data_list: list[PatternWithSupport]) -> list[PatternWithSupport]:
    """全ての結果を統合し、同一パターンのsupportを合算"""
    # パターンでソート（パターンが同じものを隣接させる）
    sorted_patterns = sorted(pattern_data_list, key=lambda x: tuple(x.pattern))

    # 同じパターンのsupportを合算
    merged_patterns = []
    for pattern, group in groupby(sorted_patterns, key=lambda x: tuple(x.pattern)):
        total_support = sum(g.support for g in group)
        merged_patterns.append((list(pattern), total_support))

    # supportで降順ソート
    return sorted(merged_patterns, key=lambda x: x.support, reverse=True)


def process_all_patterns_parallel(owner: str, repo: str, start_year: int, end_year: int):
    # 全ての入力パスを生成
    input_paths = [
        path.RESULTS / owner / f"{year}to{year + 1}" / f"{repo}.json"
        for year in range(start_year, end_year)
    ]

    # 並列処理で各ファイルを処理
    results = Parallel(n_jobs=-1, verbose=10)(
        delayed(process_single_repo_year)(input_path)
        for input_path in input_paths
    )

    # 平坦化: 二次元リストから要素を取り出して一次元にする
    flat_results:list[PatternWithSupport] = list(chain.from_iterable(results)) # type: ignore

    # 結果を統合
    merged_results = merge_pattern_results(flat_results)

    # 結果を保存
    output_path = path.RESULTS / owner / "all" / f"merged_{owner}.json"
    dump_to_json(
        [result.to_dict for result in merged_results],
        output_path
    )

if __name__ == "__main__":
    owner = "openstack"
    repos = ["nova", "cinder", "glance", "keystone", "neutron", "swift"]
    start_year = 2016
    end_year = 2025

    for repo in repos:
        process_all_patterns_parallel(owner, repo, start_year, end_year)
