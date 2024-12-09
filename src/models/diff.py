from dataclasses import dataclass


@dataclass
class DiffHunk:
    """差分のhunkを表現するデータクラス"""

    condition: list[str]
    consequent: list[str]


@dataclass
class DiffData:
    file_name: str
    pr_number: int
    base_hash: str
    target_hash: str
    diff_hunk: DiffHunk
