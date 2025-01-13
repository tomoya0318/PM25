from pathlib import Path
from joblib import Parallel, delayed

from abstractor.abstraction import abstract_code
from constants import path
from gumtree.extractor import extract_update_code_changes
from gumtree.runner_in_docker import run_GumTree
from models.diff import DiffHunk
from models.gerrit import DiffData
from models.gumtree import UpdateChange
from pattern.diff2sequence import compute_token_diff
from pattern.prefix_span import PrefixSpan
from utils.diff_handler import DiffDataHandler
from utils.lang_identifiyer import identify_lang_from_file
from utils.file_processor import dump_to_json


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

    if (
        len(abstracted_diff.condition) != len(abstracted_diff.consequent)
        or len(abstracted_diff.condition) == 1
    ):
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


def parallel_extract_and_token_diff(file_path: Path) -> list[list[str]]:
    data_list = DiffDataHandler.load_from_json(file_path)

    # diff_item_list の型を指定
    diff_item_list = list(
        Parallel(n_jobs=-1, verbose=10)(
            delayed(extract_diff_single)(item) for item in data_list
        )
    )
    # 平坦化: 二次元リストから要素を取り出して一次元にする
    diff_items: list[tuple[str, DiffHunk]] = [x for sublist in diff_item_list for x in sublist] # type: ignore

    token_diff_results = Parallel(n_jobs=-1, verbose=10)(
        delayed(compute_token_diff)(language, diff_hunk)
        for (language, diff_hunk) in diff_items # type: ignore
    )

    return token_diff_results # type: ignore

def _has_change_pattern(pattern: list[str]) -> bool:
        return len(pattern) > 1 and any(token.startswith(("+", "-")) for token in pattern)

if __name__ == "__main__":
    owner = "openstack"
    repos = ["neutron"]
    start_year = 2013
    end_year = 2014
    for repo in repos:
        for year in range(start_year, end_year):
            input_path = path.RESOURCE / owner / f"{year}to{year + 1}" / f"{repo}.json"
            output_path = path.RESULTS / owner / f"{year}to{year + 1}" / f"{repo}.json"

            print("getting diffs...")
            sequences = parallel_extract_and_token_diff(input_path)
            tmp_path = path.INTERMEDIATE/owner/f"{year}to{year + 1}"/f"{repo}.json"
            try:
                dump_to_json(sequences, tmp_path)
            except:
                print(sequences)


            print("create pattern")
            min_support = 2
            prefix_span = PrefixSpan(min_support)
            patterns = prefix_span.fit(sequences)

            filtered_patterns = [(pattern, support) for pattern, support in patterns if _has_change_pattern(pattern)]
            result = [{"pattern": pattern, "support": support} for pattern, support in filtered_patterns]
            dump_to_json(result, output_path)
