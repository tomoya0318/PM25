from concurrent.futures import ProcessPoolExecutor, as_completed
from constants import path
from utils.file_processor import load_from_json, dump_to_json, extract_project_name
from utils.ast_checker import are_ast_equal
from pattern.source_preprocessor import extract_diff
from pattern.converter import extract_trigger_sequence, extract_pattern_change
from pattern.source_preprocessor import variable_name_preprocessing
from tqdm import tqdm
import math
from collections import defaultdict


def _contains_plus_and_minus(pattern):
    contains_minus = any(token.startswith("-") for token in pattern)
    contains_plus = any(token.startswith("+") for token in pattern)
    return contains_minus and contains_plus

def _is_subpattern(small_pattern, big_pattern):
    small = set(small_pattern)
    big = set(big_pattern)
    return small.issubset(big)

def filter_pattern_chunk(pattern_chunk, sorted_patterns, patch_pairs, threshold):
    filtered_patterns = []
    sorted_pattern_list = [item['pattern'] for item in sorted_patterns]
    for item in pattern_chunk:
        pattern = item['pattern']
        support = item['support']
        if not _contains_plus_and_minus(pattern):
            continue

        duplicate_found = False
        for larger_pattern in sorted_pattern_list:
            if larger_pattern == pattern:
                break
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
            
            if not are_ast_equal(trigger_sequence, condition):
                continue
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

        filtered_patterns.append({"pattern": pattern, "support": support, "confidence": confidence})

    return filtered_patterns

def aggregate_patterns(filtered_patterns_chunks):
    aggregated_patterns = defaultdict(lambda: {'confidences': [], 'support': 0})
    for chunk in filtered_patterns_chunks:
        for pattern_entry in chunk:
            pattern_str = str(pattern_entry["pattern"])
            aggregated_patterns[pattern_str]['confidences'].append(pattern_entry["confidence"])
            aggregated_patterns[pattern_str]['support'] += pattern_entry["support"]

    # Aggregate confidence by averaging the summed confidence
    final_patterns = []
    for pattern, values in aggregated_patterns.items():
        averaged_confidence = sum(values['confidences']) / len(values['confidences'])
        final_patterns.append({"pattern": eval(pattern), "confidence": averaged_confidence, "support": values['support']})

    return final_patterns


def filter_patterns(data, patch_pairs, threshold=0.1, max_workers=20):
    sorted_data = sorted(data, key=lambda x: -len(x['pattern']))
    chunk_size = math.ceil(len(sorted_data) / max_workers)
    pattern_chunks = [sorted_data[i:i + chunk_size] for i in range(0, len(sorted_data), chunk_size)]

    filtered_patterns_chunks = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(filter_pattern_chunk, chunk, sorted_data, patch_pairs, threshold) for chunk in pattern_chunks]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Overall progress"):
            try:
                filtered_patterns_chunks.append(future.result())
            except Exception as e:
                print(f"Error processing chunk: {e}")

    return aggregate_patterns(filtered_patterns_chunks)

def process_single_project(project, pattern_path, test_path, output_path):
    print(f"Processing project: {project}")
    try:
        data = load_from_json(f"{pattern_path}/{project}")
        patch_pairs = extract_diff(f"{test_path}/{project}")
        filtered_patterns = filter_patterns(data, patch_pairs)
        dump_to_json(filtered_patterns, output_path)
    except Exception as e:
        print(f"Error processing project {project}: {e}")

def execute_parallel_single(projects, pattern_path, test_path, owner):
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = []
        for project in projects:
            output_path = f"{path.INTERMEDIATE}/pattern/filtered/{owner}/single_{project}"
            futures.append(executor.submit(process_single_project, project, pattern_path, test_path, output_path))

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

def execute_parallel_merge(projects, pattern_path, test_path, owner):
    merge_patterns = []
    projects_name = [extract_project_name(project, owner) for project in projects]
    for project in projects:
        pattern = load_from_json(f"{pattern_path}/{project}")
        patterns = [item["pattern"] for item in pattern]
        merge_patterns += patterns

    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = []
        for project in projects:
            output_path = f"{path.INTERMEDIATE}/pattern/filtered/{owner}/merged_{projects_name[0]}_{projects_name[1]}_{project}"
            futures.append(executor.submit(process_merge_project, project, merge_patterns, test_path, output_path))

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error processing project: {e}")

def prepare_data_path(owner):
    pattern_path = f"{path.INTERMEDIATE}/pattern/{owner}"
    test_path = f"{path.INTERMEDIATE}/test_data/ten_{owner}"
    return pattern_path, test_path

if __name__ == "__main__":
    owner = "numpy"

    projects = [
        "numpy_numpy_Python_master.json",
        "numpy_numpy-refactor_Python_master.json"
    ]
    pattern_path, test_path = prepare_data_path(owner)
    # execute_parallel_single(projects, pattern_path, test_path, owner)
    execute_parallel_merge(projects, pattern_path, test_path, owner)
