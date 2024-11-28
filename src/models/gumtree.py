from dataclasses import dataclass, field

from models.diff import DiffHunk


@dataclass
class Match:
    src: str
    dest: str


@dataclass
class Action:
    action: str
    tree: str
    parent: str | None = None
    at: int | None = None
    label: str | None =None


@dataclass
class GumTreeResponse:
    matches: list[Match] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)


@dataclass
class UpdateChange:
    before: str
    after: str
