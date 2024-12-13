from pathlib import Path

from constants import path
from pattern.diff2sequence import extract_diff, compute_token_diff, merge_consecutive_tokens
from utils.file_processor import dump_to_json


class PrefixSpan:
    def __init__(self, min_support):
        if not isinstance(min_support, int) or min_support < 1:
            raise ValueError("min_support must be a positive integer")
        self.min_support = min_support
        self.frequent_patterns = []

    def fit(self, sequences) -> list[tuple[list, int]]:
        if not sequences:
            return []
        if not all(isinstance(seq, (list, tuple)) for seq in sequences):
            raise ValueError("All sequences must be lists or tuples")

        self.sequences = [tuple(seq) for seq in sequences]
        self.prefix_span([], self.sequences)
        return sorted(self.frequent_patterns, key=lambda x: (-len(x[0]), -x[1]))

    def prefix_span(self, prefix, projected_db):
        if not projected_db:
            return

        freq_patterns = self.get_frequent_items(projected_db)

        for item, support in freq_patterns:
            new_prefix = prefix + [item]
            self.frequent_patterns.append((new_prefix, support))
            new_projected_db = self.build_projected_db(projected_db, item)
            if new_projected_db:  # 空の投影DBをスキップ
                self.prefix_span(new_prefix, new_projected_db)

    def get_frequent_items(self, sequences):
        items = {}
        for sequence in sequences:
            if not sequence:
                continue

            unique_items = set(sequence)
            for item in unique_items:
                items[item] = items.get(item, 0) + 1

        return sorted(
            [(item, support) for item, support in items.items() if support >= self.min_support],
            key=lambda x: (-x[1], x[0]),
        )

    def build_projected_db(self, projected_db, item):
        new_projected_db = []
        for sequence in projected_db:
            for i, current_item in enumerate(sequence):
                if current_item == item and i + 1 < len(sequence):
                    new_projected_db.append(sequence[i + 1 :])
                    break
        return new_projected_db


def process_patch_pairs(diff_path: Path, output_path: Path):

    def _has_change_pattern(pattern: list[str]) -> bool:
        return len(pattern) > 1 and any(token.startswith(("+", "-")) for token in pattern)

    sequences = []
    for language, diff_hunk in extract_diff(diff_path):
        token_diff = compute_token_diff(language, diff_hunk)
        print(token_diff)
        sequences.append(token_diff)

    min_support = 2
    prefix_span = PrefixSpan(min_support)
    patterns = prefix_span.fit(sequences)

    filtered_patterns = [(pattern, support) for pattern, support in patterns if _has_change_pattern(pattern)]

    result = [{"pattern": pattern, "support": support} for pattern, support in filtered_patterns]
    dump_to_json(result, output_path)


if __name__ == "__main__":
    project = path.RESOURCE/"numpy"/"numpy.json"
    out_path = path.RESULTS/"numpy"/"numpy.json"
    process_patch_pairs(project, out_path)
    print("end")
    print(out_path)