from datetime import datetime
from dataclasses import dataclass

from dataclasses_json import dataclass_json, DataClassJsonMixin

@dataclass_json
@dataclass
class DiffHunk(DataClassJsonMixin):
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
    merged_date: datetime
    base_message: str
    target_message: str
