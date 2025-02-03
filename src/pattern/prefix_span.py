from constants import path
from models.pattern import PatternWithSupport
from utils.file_processor import dump_to_json


class PrefixSpan:
    def __init__(self, min_support, start_year):
        if not isinstance(min_support, int) or min_support < 1:
            raise ValueError("min_support must be a positive integer")
        self.min_support = min_support
        self.start_year = start_year
        self.frequent_patterns: list[PatternWithSupport] = []

    def fit(self, sequences) -> list[PatternWithSupport]:
        if not sequences:
            return []
        if not all(isinstance(seq, (list, tuple)) for seq in sequences):
            raise ValueError("All sequences must be lists or tuples")

        self.sequences = [tuple(seq) for seq in sequences]
        self.prefix_span([], self.sequences)
        return self.frequent_patterns

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
        too_long_sequences = []
        for sequence in sequences:
            if not sequence:
                continue
            if len(sequence) > 15:
                too_long_sequences.append(sequence)
                continue
            unique_items = set(sequence)
            for item in unique_items:
                items[item] = items.get(item, 0) + 1

        dump_to_json(too_long_sequences, path.INTERMEDIATE / f"{self.start_year}_too_long_sequences.json")
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
