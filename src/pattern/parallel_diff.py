import gc
import logging
from pathlib import Path

from joblib import Parallel, delayed

from abstractor.abstraction import abstract_code
from constants import path
from gumtree.extractor import extract_update_code_changes
from gumtree.runner_in_docker import run_GumTree
from models.diff import DiffHunk
from models.gerrit import DiffData
from models.gumtree import UpdateChange
from models.pattern import PatternWithSupport
from pattern.diff2sequence import compute_token_diff
from pattern.merge import process_all_patterns_parallel
from pattern.prefix_span import PrefixSpan
from rq1.filter import parallel_process
from rq1.term import contains_all_bracket_pairs, is_all_symbols
from utils.diff_handler import DiffDataHandler
from utils.discord import send_discord_notification
from utils.file_processor import dump_to_json, load_from_json
from utils.lang_identifiyer import identify_lang_from_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_diff_single(item: DiffData):
    results = []
    try:
        language = identify_lang_from_file(item.file_name)
        if language != "Python":
            return []  # 空リストを返す
    except ValueError:
        return []  # 空リストを返す

    condition = item.diff_hunk.condition
    consequent = item.diff_hunk.consequent

    if not condition or not consequent:
        return []

    abstracted_diff = abstract_code(DiffHunk(condition, consequent))

    if len(abstracted_diff.condition) > 5 or len(abstracted_diff.consequent) > 5:
        return []

    if len(abstracted_diff.condition) != len(abstracted_diff.consequent) or len(abstracted_diff.condition) == 1:
        token_diff = DiffHunk(abstracted_diff.condition, abstracted_diff.consequent)
        results.append((language, token_diff))
    else:
        response = run_GumTree(abstracted_diff.condition, abstracted_diff.consequent)
        changes: list[UpdateChange] = extract_update_code_changes(
            abstracted_diff.condition, abstracted_diff.consequent, response.actions
        )
        for change in changes:
            token_diff = DiffHunk([change.before], [change.after])
            results.append((language, token_diff))

    return results


def parallel_extract_diff(data_list: list[DiffData]) -> list[tuple[str, DiffHunk]]:
    diff_item_list = list(Parallel(n_jobs=-1, verbose=10)(delayed(extract_diff_single)(item) for item in data_list))

    # 平坦化: 二次元リストから要素を取り出して一次元にする
    diff_items: list[tuple[str, DiffHunk]] = [x for sublist in diff_item_list for x in sublist]  # type: ignore

    # ガベージコレクションでメモリ解放
    gc.collect()

    return diff_items


def parallel_compute_diff(diff_data: list[tuple[str, DiffHunk]]) -> list[list[str]]:
    token_diff_results = Parallel(n_jobs=-1, verbose=10)(
        delayed(compute_token_diff)(language, diff_hunk) for (language, diff_hunk) in diff_data
    )

    # ガベージコレクションでメモリ解放
    gc.collect()

    return token_diff_results  # type: ignore


def parallel_extract_and_token_diff(file_path: Path) -> list[list[str]]:
    data_list = DiffDataHandler.load_from_json(file_path)

    diff_data = parallel_extract_diff(data_list)
    return parallel_compute_diff(diff_data)


def _has_change_pattern(pattern: list[str]) -> bool:
    return len(pattern) > 1 and any(token.startswith(("+", "-")) for token in pattern)


def single_process(year: int):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    tmp_path = path.INTERMEDIATE / "openstack" / f"{year}to{year + 1}" / "nova.json"
    output_path = path.RESULTS / "openstack_s10_t15" / f"{year}to{year + 1}" / f"nova.json"

    logger.info(f"create pattern from {tmp_path}")
    sequences: list[list[str]] = load_from_json(tmp_path)
    logger.info("sequences: loaded")
    filtered_sequences = []
    print(f"filtering")
    for sequence in sequences:
        if is_all_symbols(sequence):
            continue
        if not contains_all_bracket_pairs(sequence):
            continue
        filtered_sequences.append(sequence)
    min_support = 10
    prefix_span = PrefixSpan(min_support, year)
    pattern_data_list = prefix_span.fit(sequences)

    logger.info("filter pattern")
    filtered_pattern_data = [
        PatternWithSupport(pattern_data.pattern, pattern_data.support)
        for pattern_data in pattern_data_list
        if _has_change_pattern(pattern_data.pattern)
    ]

    result = [
        PatternWithSupport(pattern_data.pattern, pattern_data.support).to_dict()
        for pattern_data in filtered_pattern_data
    ]

    logger.info("dump pattern")
    total = len(result)
    send_discord_notification(f"{year}to{year + 1}のパターン抽出が完了しました。\n パターン数: {total}")
    dump_to_json(result, output_path)


def main():
    base_path = path.RESULTS / "openstack_s10_t15"
    start_year = 2016
    end_year = 2025
    try:
        # パターン作成
        Parallel(n_jobs=2, verbose=10)(delayed(single_process)(year) for year in range(start_year, end_year))
        send_discord_notification("パターン作成終了")
        # 単純なマージ
        process_all_patterns_parallel("openstack_s10_t15", "nova", start_year, end_year)
        send_discord_notification("全体マージ終了")
        # フィルタリング
        parallel_process(base_path, start_year, end_year)
        send_discord_notification("end")
        logger.info("end")
    except Exception as e:
        send_discord_notification(f"エラーが発生しました {str}")


if __name__ == "__main__":
    main()
