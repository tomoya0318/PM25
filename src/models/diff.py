from dataclasses import dataclass

@dataclass
class DiffHunk:
    """差分のhunkを表現するデータクラス"""
    condition: list[str]
    consequent: list[str]

@dataclass
class FileDiff:
    """ファイルごとの差分を表現するデータクラス"""
    file_name: str
    hunks: list[DiffHunk]