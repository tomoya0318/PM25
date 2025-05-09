from dataclasses import dataclass

from dataclasses_json import DataClassJsonMixin, dataclass_json


@dataclass_json
@dataclass
class PatternWithSupport(DataClassJsonMixin):
    pattern: list[str]
    support: int


@dataclass_json
@dataclass
class PatternData(DataClassJsonMixin):
    pattern: list[str]
    support: int
    confidence: int
