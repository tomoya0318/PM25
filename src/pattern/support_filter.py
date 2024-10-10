from concurrent.futures import ThreadPoolExecutor, as_completed
from constants import path
from utils.file_processor import load_from_json, dump_to_json
from utils.ast_checker import are_ast_equal
from pattern.code2diff.source_preprocessor import extract_diff
from pattern.code2diff.converter import extract_trigger_sequence, extract_pattern_change
from pattern.code2diff.source_preprocessor import variable_name_preprocessing
from pattern.pattern_matcher import filter_patterns_by_support
from tqdm import tqdm

def _contains_plus_and_minus(pattern):
    contains_minus = any(token.startswith("-") for token in pattern)
    contains_plus = any(token.startswith("+") for token in pattern)
    return contains_minus and contains_plus

def _is_subpattern(small_pattern, big_pattern):
    small = set(small_pattern)
    big = set(big_pattern)
    return small.issubset(big)

def filter_patterns(patterns, patch_pairs, threshold=0.1):
    filtered_patterns = []
    sorted_patterns = sorted(patterns, key=lambda x: -len(x))

    for i, pattern in tqdm(enumerate(sorted_patterns), total=len(sorted_patterns), leave=False):
        if not _contains_plus_and_minus(pattern):
            continue

        duplicate_found = False
        for larger_pattern in sorted_patterns[:i]:
            if _is_subpattern(pattern, larger_pattern):
                duplicate_found = True
                break
        if duplicate_found:
            continue

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

        confidence = (
            actually_changed / triggerable_initial
            if triggerable_initial > 0
            else 0
        )

        if confidence < threshold:
            continue

        filtered_patterns.append({"pattern": pattern, "confidence": confidence})

    return filtered_patterns

def process_single_project(project, pattern_path, test_path, output_path, min_support):
    print(f"Processing project: {project}")
    try:
        patterns = load_from_json(f"{pattern_path}/{project}")
        filtered_patterns_by_support = filter_patterns_by_support(patterns, min_support)
        # pattern部分だけを抽出
        patterns_to_filter = [item["pattern"] for item in filtered_patterns_by_support]
        patch_pairs = extract_diff(f"{test_path}/{project}")
        filtered_patterns = filter_patterns(patterns_to_filter, patch_pairs)
        dump_to_json(filtered_patterns, output_path)
    except Exception as e:
        print(f"Error processing project {project}: {e}")


def execute_parallel_single(projects_with_support, pattern_path, test_path, owner):
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for project, min_support in projects_with_support.items():
            output_path = f"{path.INTERMEDIATE}/pattern/filtered/{owner}/two_{project}"
            futures.append(executor.submit(process_single_project, project, pattern_path, test_path, output_path, min_support))

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error processing project: {e}")


def process_merge_project(project, patterns, test_path, output_path):
    print(f"Processing project: {project}")
    try:
        patch_pairs = extract_diff(f"{test_path}/{project}")
        filtered_patterns = filter_patterns(patterns, patch_pairs)
        dump_to_json(filtered_patterns, output_path)
    except Exception as e:
        print(f"Error processing project {project}: {e}")


def execute_parallel_merge(projects_with_support, pattern_path, test_path, owner):
    patterns = []
    for project, min_support in projects_with_support.items():
        output_path = f"{path.INTERMEDIATE}/pattern/filtered/{owner}/two_{project}"
        pattern = load_from_json(f"{pattern_path}/{project}")
        filtered_patterns_by_support = filter_patterns_by_support(pattern, min_support)
        patterns_to_filter = [item["pattern"] for item in filtered_patterns_by_support]
        patterns.append(patterns_to_filter)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for project in projects_with_support.keys():
            futures.append(executor.submit(process_merge_project, project, patterns, test_path, output_path))

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error processing project: {e}")


def prepare_data_path(owner):
    pattern_path = f"{path.INTERMEDIATE}/pattern/prefix/{owner}"
    test_path = f"{path.INTERMEDIATE}/test_data/{owner}"
    return pattern_path, test_path

if __name__ == "__main__":
    owner = "numpy"
    projects_with_support = {
        "numpy_numpy_Python_master.json": 2,
        "numpy_numpydoc_Python_master.json": 2,
        "numpy_numpy-financial_Python_master.json": 2
    }
    pattern_path, test_path = prepare_data_path(owner)
    execute_parallel_merge(projects_with_support, pattern_path, test_path)

        # "numpy_numpy-financial_Python_master.json": 2,
        # "numpy_numpydoc_Python_master.json": 2
