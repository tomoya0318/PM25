from joblib import Parallel, delayed
from pathlib import Path
from itertools import chain, groupby

from constants import path
from models.pattern import PatternWithSupport
from utils.file_processor import load_from_json, dump_to_json


def load_single_repo_year(input_path: Path) -> list[PatternWithSupport]:
    if not input_path.exists():
        print(f"{input_path} is not exist")
        return []

    pattern_data_list = [
        PatternWithSupport.from_dict(item) for item in load_from_json(input_path)
    ]

    return pattern_data_list


def merge_pattern_results(pattern_data_list: list[PatternWithSupport]) -> list[PatternWithSupport]:
    """全ての結果を統合し、同一パターンのsupportを合算"""
    # パターンでソート（パターンが同じものを隣接させる）
    sorted_patterns = sorted(pattern_data_list, key=lambda x: tuple(x.pattern))

    # 同じパターンのsupportを合算
    merged_patterns = []
    for pattern, group in groupby(sorted_patterns, key=lambda x: tuple(x.pattern)):
        total_support = sum(g.support for g in group)
        merged_patterns.append(PatternWithSupport(list(pattern), total_support))

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
        delayed(load_single_repo_year)(input_path)
        for input_path in input_paths
    )

    # 平坦化: 二次元リストから要素を取り出して一次元にする
    flat_results:list[PatternWithSupport] = list(chain.from_iterable(results)) # type: ignore

    # 結果を統合
    merged_results = merge_pattern_results(flat_results)

    # 結果を保存
    output_path = path.RESULTS / owner / "all" / f"merged_{owner}.json"
    dump_to_json(
        [result.to_dict() for result in merged_results],
        output_path
    )
