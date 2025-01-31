from itertools import chain, islice
from pathlib import Path

from joblib import Parallel, delayed

from constants import path
from models.pattern import PatternWithSupport
from pattern.merge import merge_pattern_results
from rq1.cut import iter_json_items
from rq1.term import is_all_symbols, is_change_pattern, remove_subset_patterns
from utils.discord import send_discord_notification
from utils.file_processor import dump_to_json, load_from_json


def single_pre_process(base_path: Path, year: int) -> list[PatternWithSupport]:
    input_path = base_path / f"{year}to{year + 1}" / "nova.json"
    output_path = base_path / f"{year}to{year + 1}" / "filtered_nova.json"

    # パターンの読み込み
    data = load_from_json(input_path)
    patterns = [PatternWithSupport.from_dict(item) for item in data]

    # 変更パターン以外を削除
    changed_pattern = [pattern for pattern in patterns if is_change_pattern(pattern.pattern)]
    # 部分パターンを削除
    unique_patterns = remove_subset_patterns(changed_pattern)

    # 保存
    unique_data = [pattern.to_dict() for pattern in unique_patterns]
    dump_to_json(unique_data, output_path)

    return unique_patterns


def single_filter_process(input_path: Path):
    count = 0
    BATCH = 100000
    result = []
    while True:
        print(count)
        data = list(islice(iter_json_items(input_path), count * BATCH, (count + 1) * BATCH))
        if not data:
            break
        result.extend([item for item in data if not is_all_symbols(item["pattern"])])
        count += 1

    return result


def parallel_process(base_path, start_year, end_year):
    output_path = base_path / "all" / "merged_nova.json"
    results = Parallel(n_jobs=-1, verbose=10)(
        delayed(single_pre_process)(base_path, year) for year in range(start_year, end_year)
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
    base_path = path.RESULTS / "openstack" / "all"
    input_path = base_path / "merged_15_nova_support10.json"
    output_path = base_path / "tmp.json"

    try:
        result = []
        result = single_filter_process(input_path)
        with open(base_path / "tmp.txt", "w") as f:
            for item in result:
                f.write(str(item) + "\n")
        dump_to_json(result, output_path)
        send_discord_notification("勝利")

    except Exception as e:
        # エラー内容を取得してDiscord通知
        print(e)
        send_discord_notification("敗北")
