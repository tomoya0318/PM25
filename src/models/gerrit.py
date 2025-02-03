from dataclasses import dataclass, field
from datetime import datetime

from dataclasses_json import DataClassJsonMixin, config, dataclass_json

from models.diff import DiffHunk


@dataclass
class Revision:
    hash: str
    committer: str
    subject: str
    commit_message: str
    changed_files: list[str]


@dataclass_json
@dataclass
class MetaData:
    hash: str
    committer: str
    subject: str
    commit_message: str


@dataclass_json
@dataclass
class ChangeData:
    change_id: str
    branch: str
    merged_at: datetime
    revisions: list[Revision]


@dataclass_json
@dataclass
class DiffData(DataClassJsonMixin):
    change_id: str
    branch: str
    file_name: str
    merged_at: datetime = field(metadata=config(encoder=datetime.isoformat, decoder=datetime.fromisoformat))
    diff_hunk: DiffHunk
    base: MetaData
    target: MetaData
