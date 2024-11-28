from pattern.code2diff.converter import compute_token_diff, merge_consecutive_tokens
from pattern.code2diff.source_preprocessor import extract_diff
from constants import path
from utils.file_processor import dump_to_json
from concurrent.futures import ProcessPoolExecutor, as_completed


class PrefixSpan:
    def __init__(self, min_support, max_workers=20):
        self.min_support = min_support
        self.max_workers = max_workers

    def fit(self, sequences):
        self.sequences = sequences
        self.frequent_patterns = []
        self.prefix_span([], sequences)
        return self.frequent_patterns

    def prefix_span(self, prefix, projected_db):
        # 並列化されたget_frequent_itemsを呼び出し
        freq_patterns = self.parallel_get_frequent_items(projected_db)
        for item, support in freq_patterns:
            new_prefix = prefix + [item]
            self.frequent_patterns.append((new_prefix, support))
            new_projected_db = self.build_projected_db(projected_db, item)
            self.prefix_span(new_prefix, new_projected_db)

    def get_frequent_items(self, sequences_chunk):
        items = {}
        for sequence in sequences_chunk:
            unique_items = set()
            for item in sequence:
                if item not in unique_items:
                    if item in items:
                        items[item] += 1
                    else:
                        items[item] = 1
                    unique_items.add(item)
        return items

    def parallel_get_frequent_items(self, projected_db):
        chunk_size = max(1, len(projected_db) // max(1, self.max_workers))
        chunks = [projected_db[i : i + chunk_size] for i in range(0, len(projected_db), chunk_size)]

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.get_frequent_items, chunk) for chunk in chunks]
            items_list = {}
            for future in as_completed(futures):
                items = future.result()
                for item, count in items.items():
                    if item in items_list:
                        items_list[item] += count
                    else:
                        items_list[item] = count

        return [(item, support) for item, support in items_list.items() if support >= self.min_support]

    def build_projected_db(self, projected_db, item):
        new_projected_db = []
        for sequence in projected_db:
            try:
                index = sequence.index(item)
                new_projected_db.append(sequence[index + 1 :])
            except ValueError:
                continue
        return new_projected_db


def process_patch_pairs(patch_data):
    sequences = []
    for language, condition, consequent in patch_data:
        tokens_diff = compute_token_diff(condition, consequent, language)
        if isinstance(tokens_diff, dict) and "error" in tokens_diff:
            print(f"エラーが発生しました： {tokens_diff["error"]}")
            continue
        if isinstance(tokens_diff, list) and not tokens_diff:
            continue
        merged_diff_token = merge_consecutive_tokens(tokens_diff)
        sequences.append(merged_diff_token)

    min_support = 1
    prefix_span = PrefixSpan(min_support)
    patterns = prefix_span.fit(sequences)

    # 2つ以上のトークンで構成されたパターンのみをフィルタリング
    filtered_patterns = [(pattern, support) for pattern, support in patterns if is_valid_pattern(pattern)]

    return filtered_patterns


def is_valid_pattern(pattern):
    if len(pattern) <= 1:
        return False

    has_diff_token = False
    for token in pattern:
        if token.startswith("-") or token.startswith("+"):
            has_diff_token = True
            break

    return has_diff_token


def process_project(file_path, output_path):
    patch_data = extract_diff(file_path)
    patterns = process_patch_pairs(patch_data)
    result = [{"pattern": pattern, "support": support} for pattern, support in patterns]
    dump_to_json(result, output_path)
    return output_path


if __name__ == "__main__":
    project = f"{path.INTERMEDIATE}/sample/flutter#50089.json"
    out_path = f"{path.RESULTS}/sample/flutter#50089.json"
    process_project(project, out_path)
    print("end")
