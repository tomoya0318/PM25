from tqdm import tqdm
from pattern.converter import compute_token_diff, merge_consecutive_tokens
from pattern.source_preprocessor import extract_diff
from constants import path
from utils.file_processor import list_files_in_directory, dump_to_json
from concurrent.futures import ProcessPoolExecutor, as_completed

class PrefixSpan:
    def __init__(self, min_support):
        self.min_support = min_support

    def fit(self, sequences):
        self.sequences = sequences
        self.frequent_patterns = []
        self.prefix_span([], sequences)
        return self.frequent_patterns

    def prefix_span(self, prefix, projected_db):
        freq_patterns = self.get_frequent_items(projected_db)
        for (item, support) in tqdm(freq_patterns, desc="Generating patterns", leave=False):
            new_prefix = prefix + [item]
            self.frequent_patterns.append((new_prefix, support))
            new_projected_db = self.build_projected_db(projected_db, item)
            self.prefix_span(new_prefix, new_projected_db)

    def get_frequent_items(self, projected_db):
        items = {}
        for sequence in projected_db:
            unique_items = set()
            for item in sequence:
                if item not in unique_items:
                    if item in items:
                        items[item] += 1
                    else:
                        items[item] = 1
                    unique_items.add(item)
        return [(item, support) for item, support in items.items() if support >= self.min_support]

    def build_projected_db(self, projected_db, item):
        new_projected_db = []
        for sequence in projected_db:
            try:
                index = sequence.index(item)
                new_projected_db.append(sequence[index + 1:])
            except ValueError:
                continue
        return new_projected_db

def process_patch_pairs(patch_pairs):
    sequences = []
    for condition, consequent in tqdm(patch_pairs, desc="Processing patch pairs", leave=False):
        diff_tokens = compute_token_diff(condition, consequent)
        if not diff_tokens:
            continue
        merged_diff_token = merge_consecutive_tokens(diff_tokens)
        sequences.append(merged_diff_token)
    
    min_support = 2
    prefix_span = PrefixSpan(min_support)
    patterns = prefix_span.fit(sequences)

    return patterns

def process_project(file_path, output_path):
    patch_pairs = extract_diff(file_path)
    patterns = process_patch_pairs(patch_pairs)
    result = [{"pattern": pattern, "support": support} for pattern, support in patterns]
    dump_to_json(result, output_path)
    return output_path

if __name__ == "__main__":
    owner = "numpy"
    dir_path = f"{path.INTERMEDIATE}/train_data/{owner}"
    projects = list_files_in_directory(dir_path)
    tasks = []
    with ProcessPoolExecutor() as executor:
        for project in projects:
            file_path = f"{dir_path}/{project}"
            output_path = f"{path.INTERMEDIATE}/pattern/prefix/{owner}/{project}"
            tasks.append(executor.submit(process_project, file_path, output_path))

        for future in tqdm(as_completed(tasks), total=len(tasks), desc="Processing projects"):
            try:
                result = future.result()
                print(f"Completed processing {result}")
            except Exception as e:
                print(f"Error processing project: {e}")
