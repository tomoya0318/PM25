from pathlib import Path

from constants import path
from models.pattern import PatternWithSupport
from pattern.diff2sequence import extract_diff, compute_token_diff
from utils.file_processor import dump_to_json, load_from_json


class PrefixSpan:
    def __init__(self, min_support):
        if not isinstance(min_support, int) or min_support < 1:
            raise ValueError("min_support must be a positive integer")
        self.min_support = min_support
        self.frequent_patterns:list[PatternWithSupport] = []

    def fit(self, sequences) -> list[PatternWithSupport]:
        if not sequences:
            return []
        if not all(isinstance(seq, (list, tuple)) for seq in sequences):
            raise ValueError("All sequences must be lists or tuples")

        self.sequences = [tuple(seq) for seq in sequences]
        self.prefix_span([], self.sequences)
        return sorted(
            self.frequent_patterns, key=lambda x: (-len(x.pattern), -x.support)
        )

    def prefix_span(self, prefix, projected_db):
        if not projected_db:
            return

        freq_patterns = self.get_frequent_items(projected_db)

        for item, support in freq_patterns:
            new_prefix = prefix + [item]
            self.frequent_patterns.append(PatternWithSupport(new_prefix, support))
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


def _has_change_pattern(pattern: list[str]) -> bool:
    return len(pattern) > 1 and any(token.startswith(("+", "-")) for token in pattern)

def process_patch_pairs(diff_path: Path, output_path: Path):


    sequences = []
    for _, language, diff_hunk in extract_diff(diff_path):
        token_diff = compute_token_diff(language, diff_hunk)
        sequences.append(token_diff)

    min_support = 2
    prefix_span = PrefixSpan(min_support)
    pattern_data_list = prefix_span.fit(sequences)

    filtered_pattern_data = [
        PatternWithSupport(pattern_data.pattern, pattern_data.support)
        for pattern_data in pattern_data_list
        if _has_change_pattern(pattern_data.pattern)
    ]

    result = [
        PatternWithSupport(pattern_data.pattern, pattern_data.support).to_dict
        for pattern_data in filtered_pattern_data
    ]
    dump_to_json(result, output_path)


if __name__ == "__main__":
    owner = "openstack"
    repos = ["nova"]
    start_year = 2013
    end_year = 2014
    for repo in repos:
        for year in range(start_year, end_year):
            input_path = path.INTERMEDIATE / owner / f"{year}to{year + 1}" / f"{repo}.json"
            output_path = path.RESULTS / owner / f"{year}to{year + 1}" / f"{repo}1.json"
            print(f"year: {year}")
            sequences = load_from_json(input_path)
            min_support = 100
            prefix_span = PrefixSpan(min_support)
            pattern_data_list = prefix_span.fit(sequences)
            filtered_pattern_data = [
                PatternWithSupport(pattern_data.pattern, pattern_data.support)
                for pattern_data in pattern_data_list
                if _has_change_pattern(pattern_data.pattern)
            ]

            result = [
                PatternWithSupport(pattern_data.pattern, pattern_data.support).to_dict
                for pattern_data in filtered_pattern_data
            ]

            dump_to_json(result, output_path)
    print("end")
