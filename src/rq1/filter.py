from itertools import chain, islice
from pathlib import Path

from joblib import Parallel, delayed

from constants import path
from models.pattern import PatternWithSupport
from pattern.merge import merge_pattern_results
from rq1.term import contains_all_bracket_pairs, is_all_symbols, is_change_pattern, remove_subset_patterns
from utils.discord import send_discord_notification
from utils.file_processor import dump_to_json, load_from_json, stream_json_patterns


def single_pre_process(base_path: Path, year: int) -> list[PatternWithSupport]:
    input_path = base_path / f"{year}to{year + 1}" / "nova.json"
    output_path = base_path / f"{year}to{year + 1}" / "filtered_nova.json"

    # パターンの読み込み
    data = load_from_json(input_path)
    patterns = [PatternWithSupport.from_dict(item) for item in data]

    # 変更パターン以外を削除
    # changed_pattern = [pattern for pattern in patterns if is_change_pattern(pattern.pattern)]
    # 部分パターンを削除
    unique_patterns = remove_subset_patterns(patterns)

    # 保存
    unique_data = [pattern.to_dict() for pattern in unique_patterns]
    dump_to_json(unique_data, output_path)

    return unique_patterns


def process_chunk_filter(chunk: list[dict]) -> list[PatternWithSupport]:
    filtered_pattern = []
    for item in chunk:
        try:
            pattern = PatternWithSupport.from_dict(item)
            if is_all_symbols(pattern.pattern):
                continue
            if not contains_all_bracket_pairs(pattern.pattern):
                continue
            filtered_pattern.append(pattern)
        except Exception as e:
            print(f"アイテムの処理エラー: {str(e)}")
    return filtered_pattern


def parallel_filtering(file_path: Path, chunk_size: int = 1000, n_jobs: int = -1) -> list[PatternWithSupport]:
    patterns = stream_json_patterns(file_path)
    filtered_chunks = Parallel(n_jobs=n_jobs, verbose=10)(
        delayed(process_chunk_filter)(chunk)
        for chunk in iter(lambda: list(islice(patterns, chunk_size)), [])
        if chunk  # 空チャンクをスキップ
    )
    filtered_patterns = list(chain.from_iterable(filtered_chunks))  # type: ignore
    return filtered_patterns


def count_filter_term_from_sequence(base_path: Path, year: int):
    input_path = base_path / f"{year}to{year + 1}" / "nova.json"
    sequence_data: list[list[str]] = load_from_json(input_path)
    all = len(sequence_data)
    all_symbol_count = 0
    not_bracket_pair_count = 0
    for sequence in sequence_data:
        try:
            if is_all_symbols(sequence):
                all_symbol_count += 1
            if not contains_all_bracket_pairs(sequence):
                not_bracket_pair_count += 1
        except Exception as e:
            print(f"アイテムの処理エラー: {str(e)}")
    return all, all_symbol_count, not_bracket_pair_count


def parallel_process(base_path: Path, start_year: int, end_year: int):
    """"""

    def _subset_filter(year: int) -> list[PatternWithSupport]:
        input_path = base_path / f"{year}to{year + 1}" / "nova.json"

        data = load_from_json(input_path)
        patterns = [PatternWithSupport.from_dict(item) for item in data]

        # 部分パターン削除
        subset_patterns = remove_subset_patterns(patterns)
        # 保存
        subset_path = base_path / f"{year}to{year + 1}" / "subset_nova.json"
        subset_patterns_dict = [pattern.to_dict() for pattern in subset_patterns]
        dump_to_json(subset_patterns_dict, subset_path)

        return subset_patterns

    results = Parallel(n_jobs=-1, verbose=10)(delayed(_subset_filter)(year) for year in range(start_year, end_year))
    flat_results: list[PatternWithSupport] = list(chain.from_iterable(results))  # type: ignore
    send_discord_notification("年ごとの重複削除完了")

    merged_patterns = merge_pattern_results(flat_results)
    not_subset = remove_subset_patterns(merged_patterns)

    # 構造エラーのものを削除
    custom_filtered_patterns = []
    for pattern in not_subset:
        if is_all_symbols(pattern.pattern):
            continue
        if not contains_all_bracket_pairs(pattern.pattern):
            continue
        custom_filtered_patterns.append(pattern)

    custom_path = base_path / "all" / "filtered_now_nova.json"
    dump_to_json(custom_filtered_patterns, custom_path)
    send_discord_notification(
        f"カスタムフィルタリング完全終了\n 構造エラーの数: {len(merged_patterns) - len(custom_filtered_patterns)}"
    )

    # 変更パターン以外削除
    no_change_patterns = [pattern for pattern in not_subset if is_change_pattern(pattern.pattern)]

    no_change_path = base_path / "all" / "pre_filtered_full_nova.json"
    dump_to_json(no_change_patterns, no_change_path)
    send_discord_notification("従来研究のフィルタリング終了")


def parallel_count_sequnce_filter():
    base_path = path.INTERMEDIATE / "openstack"
    start_year = 2016
    end_year = 2025
    result: list[tuple[int, int, int]] = Parallel(n_jobs=-1, verbose=10)(
        delayed(count_filter_term_from_sequence)(base_path, year) for year in range(start_year, end_year)
    )  # type: ignore

    total, symbol_count, invalid_bracket_count = 0, 0, 0
    for full, symbol, bracket in result:
        total += full
        symbol_count += symbol
        invalid_bracket_count += bracket
    print(f"total: {total}\n all_symbol: {symbol_count}\n invalid_bracket: {invalid_bracket_count}\n")


if __name__ == "__main__":
    base_path = path.RESULTS / "openstack_s10_t15"
    start_year = 2013
    end_year = 2025
    try:
        parallel_process(base_path, start_year, end_year)
        send_discord_notification("end")

    except Exception as e:
        # エラー内容を取得してDiscord通知
        print(e)
        send_discord_notification("敗北")
