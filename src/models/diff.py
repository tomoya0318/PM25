from dataclasses import dataclass


@dataclass
class DiffHunk:
    """差分のhunkを表現するデータクラス"""

    condition: list[str]
    consequent: list[str]
